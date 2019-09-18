import asyncio
import aiohttp
import requests

from presqt.targets.github.utilities import (
    get_page_total, validation_check, github_paginated_data, download_content)
from presqt.utilities import (PresQTInvalidTokenError, PresQTValidationError, 
                              PresQTResponseException, get_dictionary_from_list)


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
        User's OSF token

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers=header) as response:
        assert response.status == 200
        content =  await response.read()
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
        User's OSF token

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
    ˇ
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
        See https://app.gitbook.com/@crc-nd/s/presqt/project-description/developer-documentation/code-documentation/resource-download for details
    - List of string paths representing empty containers that must be written.
        Example: ['empty/folder/to/write/', 'another/empty/folder/]
    """
    try:
        username, header = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.',
                                      status.HTTP_401_UNAUTHORIZED)

    data = github_paginated_data(username, token, header)

    for entry in data:
        if entry['id'] == int(resource_id):
            repo_name = entry['name']
            break
    # Get initial data from first page of data
    initial_url = "https://api.github.com/repos/{}/{}/contents".format(username, repo_name)
    files, empty_containers = download_content(initial_url, header, repo_name, [])
    file_urls = [file['file'] for file in files]

    loop = asyncio.new_event_loop()
    download_data = loop.run_until_complete(async_main(file_urls, header))
    # Go through the file dictionaries and replace the file class with the binary_content
    for file in files:
        file['file'] = get_dictionary_from_list(download_data,'url', file['file'])['binary_content']

    return files, empty_containers
