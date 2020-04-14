import asyncio
import aiohttp
import requests

from rest_framework import status

from presqt.targets.github.utilities import (
    validation_check, github_paginated_data, download_content)
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
    header: str
        Header for request

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers=header) as response:
        assert response.status == 200
        content = await response.read()
        return {'url': url, 'binary_content': content}


async def async_main(url_list, header):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call
    header: str
        Header for request

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, header) for url in url_list])


def github_download_resource(token, resource_id):
    """
    Fetch the requested resource from GitHub along with its hash information.

    Parameters
    ----------
    token : str
        User's GitHub token
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
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    project_url = 'https://api.github.com/repositories/{}'.format(resource_id)

    response = requests.get(project_url, headers=header)

    if response.status_code != 200:
        raise PresQTResponseException(
            'The resource with id, {}, does not exist for this user.'.format(resource_id),
            status.HTTP_404_NOT_FOUND)
    data = response.json()

    repo_name = data['name']
    # Strip off the unnecessary {+path} that's included in the url
    # Example: https://api.github.com/repos/eggyboi/djangoblog/contents/{+path} becomes
    # https://api.github.com/repos/eggyboi/djangoblog/contents
    contents_url = data['contents_url'].partition('/{+path}')[0]

    files, empty_containers, action_metadata = download_content(
        username, contents_url, header, repo_name, [])
    file_urls = [file['file'] for file in files]

    loop = asyncio.new_event_loop()
    download_data = loop.run_until_complete(async_main(file_urls, header))
    # Go through the file dictionaries and replace the file path with the binary_content
    for file in files:
        file['file'] = get_dictionary_from_list(
            download_data, 'url', file['file'])['binary_content']

    return {
        'resources': files,
        'empty_containers': empty_containers,
        'action_metadata': action_metadata
    }
