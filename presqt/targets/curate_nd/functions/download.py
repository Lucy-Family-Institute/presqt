import asyncio
import os

import aiohttp
import requests

from rest_framework import status

from presqt.targets.curate_nd.utilities import get_curate_nd_resource
from presqt.targets.curate_nd.classes.main import CurateND
from presqt.utilities import (PresQTInvalidTokenError, PresQTValidationError,
                              get_dictionary_from_list)


async def async_get(url, session, token):
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

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers={'X-Api-Token': token}) as response:
        assert response.status == 200
        content = await response.read()
        md5 = response.headers['Content-Md5']
        return {'url': url, 'binary_content': content, 'md5': md5}


async def async_main(url_list, token):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call
    token: str
        User's CurateND token

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, token) for url in url_list])


def curate_nd_download_resource(token, resource_id):
    """
    Fetch the requested resource from CurateND along with its hash information.

    Parameters
    ----------
    token : str
        User's CurateND token
    resource_id : str
        ID of the resource requested

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
                            'metadata': {
                                'sourcePath': '/full/path/at/source.jpg',
                                'title': 'file_title',
                                'sourceHashes': {'hash_algorithm': 'the_hash'},
                                'extra': {'any': 'extra'}
                             }
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

    # Get the resource
    resource = get_curate_nd_resource(resource_id, curate_instance)

    # Get all the files for the provided resources.
    files = []
    empty_containers = []
    if resource.kind_name == 'file':
        action_metadata = {"sourceUsername": resource.extra['depositor']}
        # Get the title of the Project to add to sourcePath
        project_title = requests.get(resource.extra['isPartOf'],
                                     headers={'X-Api-Token': '{}'.format(token)}).json()['title']
        file_metadata = {
            "sourcePath": '/{}/{}'.format(project_title,resource.title),
            "title": resource.title,
            "sourceHashes": {
                "md5": resource.md5},
            "extra": resource.extra
        }

        # This is so we aren't missing the few extra keys that are pulled out for the PresQT payload
        file_metadata['extra'].update(
            {"id": resource.id, "date_submitted": resource.date_submitted})

        binary_file, curate_hash = resource.download()

        files.append({
            'file': binary_file,
            'hashes': {'md5': curate_hash},
            'title': resource.title,
            # If the file is the only resource we are downloading then we don't need it's full path.
            'path': '/{}'.format(resource.title),
            'metadata': file_metadata})

    else:
        action_metadata = {"sourceUsername": resource.extra['depositor']}

        if not resource.extra['containedFiles']:
            empty_containers.append('{}'.format(resource.title))
        else:
            title_helper = {}
            file_urls = []
            project_title = resource.title
            file_metadata = []
            for file in resource.extra['containedFiles']:
                # That gross md5 search
                md5_end = '</md5checksum>'
                md5_hash_check = file['characterization'].partition(md5_end)[0]
                # Md5 hashes are 32 characters...
                file_md5 = md5_hash_check[len(md5_hash_check)-32:]

                file_metadata_dict = {
                    "sourcePath": '/{}/{}'.format(project_title, file['label']),
                    "title": file['label'],
                    "sourceHashes": {
                        "md5": file_md5},
                    "extra": {}}
                for key, value in file.items():
                    if key not in ['label', 'depositor']:
                        file_metadata_dict['extra'][key] = value
                file_metadata.append(file_metadata_dict)

                title_helper[file['downloadUrl']] = file['label']
                file_urls.append(file['downloadUrl'])

            loop = asyncio.new_event_loop()
            download_data = loop.run_until_complete(async_main(file_urls, token))

            for file in download_data:
                files.append({
                    'file': file['binary_content'],
                    'hashes': {'md5': file['md5']},
                    'title': title_helper[file['url']],
                    'path': '/{}/{}'.format(resource.title, title_helper[file['url']]),
                    'metadata': get_dictionary_from_list(file_metadata, 'title',
                                                         title_helper[file['url']])})

    return {
        'resources': files,
        'empty_containers': empty_containers,
        'action_metadata': action_metadata
    }
