import asyncio
import aiohttp
import requests

from rest_framework import status

from presqt.targets.osf.utilities import get_osf_resource, osf_download_metadata
from presqt.utilities import (PresQTResponseException, PresQTInvalidTokenError,
                              get_dictionary_from_list, update_process_info, increment_process_info,
                              update_process_info_message)
from presqt.targets.osf.classes.main import OSF


async def async_get(url, session, token, process_info_path):
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
        User's OSF token
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers={'Authorization': 'Bearer {}'.format(token)}) as response:
        assert response.status == 200
        content = await response.read()
        # Increment the number of files done in the process info file.
        increment_process_info(process_info_path, 'resource_download')
        return {'url': url, 'binary_content': content}


async def async_main(url_list, token, process_info_path):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call
    token: str
        User's OSF token
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, token, process_info_path) for url in url_list])


def osf_download_resource(token, resource_id, process_info_path):
    """
    Fetch the requested resource from OSF along with its hash information.

    Parameters
    ----------
    token : str
        User's OSF token
    resource_id : str
        ID of the resource requested
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

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
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    # Get contributor name
    contributor_name = requests.get('https://api.osf.io/v2/users/me/',
                                    headers={'Authorization': 'Bearer {}'.format(token)}).json()[
                                        'data']['attributes']['full_name']
    action_metadata = {"sourceUsername": contributor_name}
    # Get the resource
    resource = get_osf_resource(resource_id, osf_instance)

    # Get all files for the provided resources.
    # The 'path' value will be the path that the file is eventually saved in. The root of the
    # path should be the resource.
    files = []
    empty_containers = []
    if resource.kind_name == 'file':
        # Add the total number of projects to the process info file.
        # This is necessary to keep track of the progress of the request.
        update_process_info(process_info_path, 1, 'resource_download')
        update_process_info_message(process_info_path, 'resource_download',
                                    'Downloading file from OSF...')

        project = osf_instance.project(resource.parent_project_id)
        files.append({
            "file": resource.download(),
            "hashes": resource.hashes,
            "title": resource.title,
            # If the file is the only resource we are downloading then we don't need it's full path
            "path": '/{}'.format(resource.title),
            "source_path": '/{}/{}{}'.format(project.title, resource.provider, resource.materialized_path),
            "extra_metadata": osf_download_metadata(resource)
        })
        # Increment the number of files done in the process info file.
        increment_process_info(process_info_path, 'resource_download')
    else:
        if resource.kind_name == 'project':
            resource.get_all_files('', files, empty_containers)
            project = resource
        elif resource.kind_name == 'storage':
            resource.get_all_files('/{}'.format(resource.title), files, empty_containers)
            project = osf_instance.project(resource.node)
        else:
            resource.get_all_files('', files, empty_containers)
            project = osf_instance.project(resource.parent_project_id)
            for file in files:
                # File Path needs to start at the folder and strip everything before it.
                # Example: If the resource is 'Docs2' and the starting path is
                # '/Project/Storage/Docs1/Docs2/file.jpeg' then the final path
                # needs to be '/Docs2/file.jpeg'
                path_to_strip = resource.materialized_path[:-(len(resource.title) + 2)]
                file['path'] = file['file'].materialized_path[len(path_to_strip):]

        file_urls = [file['file'].download_url for file in files]

        # Add the total number of projects to the process info file.
        # This is necessary to keep track of the progress of the request.
        update_process_info(process_info_path, len(file_urls), 'resource_download')
        update_process_info_message(process_info_path, 'resource_download',
                                    'Downloading files from OSF...')

        # Asynchronously make all download requests
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        download_data = loop.run_until_complete(async_main(file_urls, token, process_info_path))

        # Go through the file dictionaries and replace the file class with the binary_content
        for file in files:
            file['source_path'] = '/{}/{}{}'.format(project.title,
                                                    file['file'].provider,
                                                    file['file'].materialized_path)
            file['file'] = get_dictionary_from_list(
                download_data, 'url', file['file'].download_url)['binary_content']

    return {
        'resources': files,
        'empty_containers': empty_containers,
        'action_metadata': action_metadata
    }
