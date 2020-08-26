import asyncio

import aiohttp
import requests

from rest_framework import status

from presqt.targets.curate_nd.utilities import get_curate_nd_resource
from presqt.targets.curate_nd.classes.main import CurateND
from presqt.utilities import (PresQTInvalidTokenError, PresQTValidationError,
                              get_dictionary_from_list, update_process_info_download, increment_process_info_download,
                              update_process_info_message)


async def async_get(url, session, token, process_info_path, action):
    """
    Coroutine that uses aiohttp to make a GET request. This is the method that will be called
    asynchronously with other GETs.

    Parameters
    ----------
    url: str
        URL to call
    session: ClientSession object
        aiohttp ClientSession Object
    token: str
        User's CurateND token
    process_info_path: str
        Path to the process info file that keeps track of the action's progress
    action: str
        The action being performed

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers={'X-Api-Token': token}) as response:
        assert response.status == 200
        content = await response.read()
        # Increment the number of files done in the process info file.
        increment_process_info_download(process_info_path, action)
        return {'url': url, 'binary_content': content}


async def async_main(url_list, token, process_info_path, action):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call
    token: str
        User's CurateND token
    process_info_path: str
        Path to the process info file that keeps track of the action's progress
    action: str
        The action being performed

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, token, process_info_path, action) for url in url_list])


def curate_nd_download_resource(token, resource_id, process_info_path, action):
    """
    Fetch the requested resource from CurateND along with its hash information.

    Parameters
    ----------
    token : str
        User's CurateND token
    resource_id : str
        ID of the resource requested
    process_info_path: str
        Path to the process info file that keeps track of the action's progress
    action: str
        The action being performed

    Returns
    -------
    Dictionary with the following keys: values
        'resources': List of dictionary objects that each hold a file and its information.
                     Dictionary must be in the following format:
                         {
                            'file': binary_file,
                            'hashes': {'hash_algorithm': 'the_hash'},
                            'title': 'file.jpg',
                            'path': '/path/to/file',
                            'source_path: '/full/path/to/file',
                            'extra_metadata': {'any': 'extra'}
                         }
        'empty_containers: List of string paths representing empty containers that must be written.
                              Example: ['empty/folder/to/write/', 'another/empty/folder/]
        'action_metadata': Dictionary containing action metadata. Must be in the following format:
                              {
                              'sourceUsername': 'some_username',
                              }
    """
    try:
        curate_instance = CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTValidationError("Token is invalid. Response returned a 401 status code.",
                                    status.HTTP_401_UNAUTHORIZED)
    
    update_process_info_message(process_info_path, action, 'Downloading files from CurateND...')

    # Get the resource
    resource = get_curate_nd_resource(resource_id, curate_instance)
    action_metadata = {"sourceUsername": resource.extra['depositor']}

    # Get all the files for the provided resources.
    files = []
    empty_containers = []
    if resource.kind_name == 'file':
        title_url = resource.extra['isPartOf']
        if type(title_url) is list:
            title_url = resource.extra['isPartOf'][0]
        # Get the title of the Project to add to sourcePath
        project_title = requests.get(title_url, headers={'X-Api-Token': '{}'.format(token)}).json()['title']

        # This is so we aren't missing the few extra keys that are pulled out for the PresQT payload
        resource.extra.update({"id": resource.id, "date_submitted": resource.date_submitted})

        # Add the total number of items to the process info file.
        # This is necessary to keep track of the progress of the request.
        update_process_info_download(process_info_path, 1, action )

        binary_file, curate_hash = resource.download()

        files.append({
            'file': binary_file,
            'hashes': {'md5': curate_hash},
            'title': resource.title,
            # If the file is the only resource we are downloading then we don't need it's full path.
            'path': '/{}'.format(resource.title),
            'source_path': '/{}/{}'.format(project_title, resource.title),
            'extra_metadata': resource.extra})

        # Increment the number of files done in the process info file.
        increment_process_info_download(process_info_path, action)

    else:
        if not resource.extra['containedFiles']:
            empty_containers.append('{}'.format(resource.title))
        else:
            # Add the total number of items to the process info file.
            # This is necessary to keep track of the progress of the request.
            update_process_info_download(process_info_path, len(resource.extra['containedFiles']), action)

            title_helper = {}
            hash_helper = {}
            file_urls = []
            project_title = resource.title
            file_metadata = []
            for file in resource.extra['containedFiles']:
                download_url = file['downloadUrl']
                contained_file = get_curate_nd_resource(file['id'], curate_instance)
                file_metadata_dict = {
                    "title": contained_file.title,
                    "extra": contained_file.extra}
                file_metadata.append(file_metadata_dict)

                title_helper[download_url] = contained_file.title
                hash_helper[download_url] = contained_file.md5
                title_helper[file['downloadUrl']] = file['label']
                file_urls.append(file['downloadUrl'])

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            download_data = loop.run_until_complete(async_main(file_urls, token, process_info_path, action))

            for file in download_data:
                title = title_helper[file['url']]
                hash = hash_helper[file['url']]
                files.append({
                    'file': file['binary_content'],
                    'hashes': {'md5': hash},
                    'title': title,
                    "source_path": '/{}/{}'.format(project_title, title),
                    'path': '/{}/{}'.format(resource.title, title),
                    'extra_metadata': get_dictionary_from_list(file_metadata, 'title', title)['extra']})

    return {
        'resources': files,
        'empty_containers': empty_containers,
        'action_metadata': action_metadata
    }
