import asyncio

import aiohttp
from rest_framework import status

from presqt.targets.osf.utilities import get_osf_resource
from presqt.utilities import (PresQTResponseException, PresQTInvalidTokenError,
                              get_dictionary_from_list)
from presqt.targets.osf.classes.main import OSF


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
        User's OSF token

    Returns
    -------
    Response JSON
    """
    async with session.get(url) as response:
        assert response.status == 200
        content =  await response.read()
        return {'url': url, 'binary_content': content}

async def async_main(url_list, token):
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
        return await asyncio.gather(*[async_get(url, session, token) for url in url_list])

def osf_download_resource(token, resource_id):
    """
    Fetch the requested resource from OSF along with its hash information.

    Parameters
    ----------
    token : str
        User's OSF token

    resource_id : str
        ID of the resource requested

    Returns
    -------
    List of dictionary objects that each hold a file and its information
    """
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    # Get the resource
    resource = get_osf_resource(resource_id, osf_instance)

    # Get all files for the provided resources.
    # The 'path' value will be the path that the file is eventually saved in. The root of the
    # path should be the resource.
    files = []
    empty_containers = []
    if resource.kind_name == 'file':
        binary_file = resource.download()
        files.append({
            'file': binary_file,
            'hashes': resource.hashes,
            'title': resource.title,
            # If the file is the only resource we are downloading then we don't need it's full path
            'path': '/{}'.format(resource.title)
        })
    else:
        if resource.kind_name == 'project':
            resource.get_all_files('', files, empty_containers)
        if resource.kind_name == 'storage':
            resource.get_all_files('/{}/'.format(resource.title), files, empty_containers)
        elif resource.kind_name == 'folder':
            resource.get_all_files('', files, empty_containers)
            for file in files:
                # File Path needs to start at the folder and strip everything before it.
                # Example: If the resource is 'Docs2' and the starting path is
                # '/Project/Storage/Docs1/Docs2/file.jpeg' then the final path
                # needs to be '/Docs2/file.jpeg'
                path_to_strip = resource.materialized_path[:-(len(resource.title) + 2)]
                file['path'] = file['file'].materialized_path[len(path_to_strip):]

        # Asynchronously make all download requests
        file_urls = [file['file'].download_url for file in files]
        loop = asyncio.new_event_loop()
        download_data = loop.run_until_complete(async_main(file_urls, token))

        # Go through the file dictionaries and replace the file class with the binary_content
        for file in files:
            file['file'] = get_dictionary_from_list(download_data,'url', file.pop('file').download_url)['binary_content']

    return files, empty_containers