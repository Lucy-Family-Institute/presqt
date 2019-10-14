import asyncio
import aiohttp

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
    token: str
        User's GitHub token

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
    token: str
        User's GitHub token

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
    - List of dictionary objects that each hold a file and its information.
        Dictionary must be in the following format:
        {
            'file': binary_file,
            'hashes': {'md5': 'the_hash},
            'title': 'file.jpg',
            'path': '/path/to/file
        }
    - List of string paths representing empty containers that must be written.
        Example: ['empty/folder/to/write/', 'another/empty/folder/']
    """
    try:
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.',
                                      status.HTTP_401_UNAUTHORIZED)

    data = github_paginated_data(token)

    for entry in data:
        if entry['id'] == int(resource_id):
            repo_name = entry['name']
            # Strip off the uneccessarry {+path} that's included in the url
            # Example: https://api.github.com/repos/eggyboi/djangoblog/contents/{+path} becomes
            # https://api.github.com/repos/eggyboi/djangoblog/contents
            contents_url = entry['contents_url'].partition('/{+path}')[0]
            break

    files, empty_containers, action_metadata = download_content(
        {'username': username, 'repo_name': repo_name}, contents_url, header, repo_name, [])
    file_urls = [file['file'] for file in files]

    loop = asyncio.new_event_loop()
    download_data = loop.run_until_complete(async_main(file_urls, header))
    # Go through the file dictionaries and replace the file path with the binary_content
    for file in files:
        file['file'] = get_dictionary_from_list(download_data, 'url', file['file'])['binary_content']

    return files, empty_containers, action_metadata