import asyncio
import aiohttp
import requests
import base64

from rest_framework import status

from presqt.targets.gitlab.utilities import (
    validation_check, gitlab_paginated_data, download_content)
from presqt.utilities import PresQTResponseException, get_dictionary_from_list


async def async_get(url, session, header):
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
        User's GitHub token

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers=header) as response:
        assert response.status == 200
        content = await response.json()
        return {
            'url': url,
            'binary_content': base64.b64decode(content['content']),
            'hashes': {'sha256': content['content_sha256']}}


async def async_main(url_list, header):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call
    token: str
        User's GitHub token

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, header) for url in url_list])


def gitlab_download_resource(token, resource_id):
    """
    Fetch the requested resource from GitLab along with its hash information.

    Parameters
    ----------
    token : str
        User's GitLab token
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
        header, user_id = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    # Get the user's GitLab username for action metadata
    username = requests.get("https://gitlab.com/api/v4/user", headers=header).json()['username']

    partitioned_id = resource_id.partition(':')
    if ':' in resource_id:
        project_id = partitioned_id[0]
    else:
        project_id = resource_id

    project_url = 'https://gitlab.com/api/v4/projects/{}'.format(project_id)

    response = requests.get(project_url, headers=header)
    if response.status_code != 200:
        raise PresQTResponseException(
            'The resource with id, {}, does not exist for this user.'.format(resource_id),
            status.HTTP_404_NOT_FOUND)

    project_name = response.json()['name']
    if ':' not in resource_id:
        # This is for a project
        all_files_url = "https://gitlab.com/api/v4/projects/{}/repository/tree?recursive=1".format(
            resource_id)
        data = gitlab_paginated_data(header, user_id, all_files_url)
        is_project = True

    elif ':' in resource_id and '%2E' not in resource_id:
        # This is for a directory
        all_files_url = "https://gitlab.com/api/v4/projects/{}/repository/tree?path={}&recursive=1".format(
            partitioned_id[0], partitioned_id[2].replace('+', ' '))
        data = gitlab_paginated_data(header, user_id, all_files_url)
        if data == []:
            raise PresQTResponseException(
                'The resource with id, {}, does not exist for this user.'.format(resource_id),
                status.HTTP_404_NOT_FOUND)
        is_project = False

    else:
        # This is a single file
        data = requests.get('https://gitlab.com/api/v4/projects/{}/repository/files/{}?ref=master'.format(
            project_id, partitioned_id[2].replace('+', ' ')), headers=header).json()
        if 'message' in data.keys():
            raise PresQTResponseException(
                'The resource with id, {}, does not exist for this user.'.format(resource_id),
                status.HTTP_404_NOT_FOUND)

        return {
            'resources': [{
                'file': base64.b64decode(data['content']),
                'hashes': {'sha256': data['content_sha256']},
                'title': data['file_name'],
                'path': '/{}'.format(data['file_name']),
                'source_path': data['file_path'],
                'extra_metadata': {}}],
            'empty_containers': [],
            'action_metadata': {'sourceUsername': username}}

    files, empty_containers, action_metadata = download_content(
        username, project_name, project_id, data, [], is_project)
    file_urls = [file['file'] for file in files]

    loop = asyncio.new_event_loop()
    download_data = loop.run_until_complete(async_main(file_urls, header))

    # Go through the file dictionaries and replace the file path with the binary_content
    # and replace the hashes with the correct file hashes
    for file in files:
        file['hashes'] = get_dictionary_from_list(
            download_data, 'url', file['file'])['hashes']
        file['file'] = get_dictionary_from_list(
            download_data, 'url', file['file'])['binary_content']

    return {
        'resources': files,
        'empty_containers': empty_containers,
        'action_metadata': action_metadata
    }