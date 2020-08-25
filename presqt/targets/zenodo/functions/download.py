import asyncio
import aiohttp
import requests

from rest_framework import status

from presqt.targets.zenodo.utilities import zenodo_download_helper, zenodo_validation_check
from presqt.utilities import (PresQTResponseException, get_dictionary_from_list,
                              update_process_info,
                              increment_process_info, update_process_info_message)


async def async_get(url, session, params, process_info_path):
    """
    Coroutine that uses aiohttp to make a GET request. This is the method that will be called
    asynchronously with other GETs.

    Parameters
    ----------
    url: str
        URL to call
    session: ClientSession object
        aiohttp ClientSession Object
    params: str
        params
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    Response JSON
    """
    async with session.get(url, params=params) as response:
        assert response.status == 200
        content = await response.read()
        # Increment the number of files done in the process info file.
        increment_process_info(process_info_path, 'resource_download')
        return {'url': url, 'binary_content': content}


async def async_main(url_list, params, process_info_path):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call
    params: str
        params
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, params, process_info_path) for url in url_list])


def zenodo_download_resource(token, resource_id, process_info_path):
    """
    Fetch the requested resource from Zenodo along with its hash information.

    Parameters
    ----------
    token : str
        User's Zenodo token
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
        auth_parameter = zenodo_validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('Token is invalid. Response returned a 401 status code.',
                                      status.HTTP_401_UNAUTHORIZED)

    update_process_info_message(process_info_path, 'resource_download',
                                    'Downloading files from Zenodo...')
    files = []
    empty_containers = []
    base_url = None

    # If the resource_id is longer than 7 characters, the resource is an individual file
    if len(resource_id) > 7:
        # First we need to check if the file id given belongs to a public published record.
        zenodo_file = requests.get(
            'https://zenodo.org/api/files/{}'.format(resource_id), params=auth_parameter)
        if zenodo_file.status_code != 200:
            # If not, we need to loop through their depositions to look for the file.
            zenodo_projects = requests.get('https://zenodo.org/api/deposit/depositions',
                                           params=auth_parameter).json()
            for entry in zenodo_projects:
                project_files = requests.get(entry['links']['self'], params=auth_parameter).json()
                for file in project_files['files']:
                    if file['id'] == resource_id:
                        base_url = entry['links']['self']
                        file_url = file['links']['self']
                        is_record = False
                        break
                else:
                    # If the file wasn't found we want to continue the loop.
                    continue
                break
        else:
            is_record = True
            base_url = 'https://zenodo.org/api/files/{}'.format(resource_id)
            file_url = 'https://zenodo.org/api/files/{}'.format(resource_id)

        if base_url is None:
            raise PresQTResponseException(
                "The resource with id, {}, does not exist for this user.".format(resource_id),
                status.HTTP_404_NOT_FOUND)

        # Add the total number of projects to the process info file.
        # This is necessary to keep track of the progress of the request.
        update_process_info(process_info_path, 1, 'resource_download')

        files, action_metadata = zenodo_download_helper(is_record, base_url, auth_parameter, files,
                                                        file_url)

        # Increment the number of files done in the process info file.
        increment_process_info(process_info_path, 'resource_download')

    # Otherwise, it's a full project
    else:
        base_url = 'https://zenodo.org/api/records/{}'.format(resource_id)
        zenodo_record = requests.get(base_url, params=auth_parameter)
        is_record = True
        if zenodo_record.status_code != 200:
            base_url = 'https://zenodo.org/api/deposit/depositions/{}'.format(resource_id)
            is_record = False
        try:
            files, action_metadata = zenodo_download_helper(is_record, base_url, auth_parameter,
                                                            files)
        except PresQTResponseException:
            raise PresQTResponseException(
                "The resource with id, {}, does not exist for this user.".format(resource_id),
                status.HTTP_404_NOT_FOUND)

        file_urls = [file['file'] for file in files]

        # Add the total number of projects to the process info file.
        # This is necessary to keep track of the progress of the request.
        update_process_info(process_info_path, len(file_urls), 'resource_download')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        download_data = loop.run_until_complete(async_main(file_urls, auth_parameter, process_info_path))

        # Go through the file dictionaries and replace the file path with the binary_content
        for file in files:
            file['file'] = get_dictionary_from_list(
                download_data, 'url', file['file'])['binary_content']

    return {
        'resources': files,
        'empty_containers': empty_containers,
        'action_metadata': action_metadata
    }
