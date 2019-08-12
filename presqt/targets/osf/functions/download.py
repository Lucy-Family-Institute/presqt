import asyncio

import aiohttp
from rest_framework import status

from presqt.utilities import (PresQTResponseException, PresQTInvalidTokenError,
                              get_dictionary_from_list)
from presqt.targets.osf.classes.main import OSF
from presqt.targets.osf.helpers import get_osf_resource


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
    async with session.get(url, headers={'Authorization': 'Bearer {}'.format(token)}) as response:
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
        file_data = []
        file_urls = []
        for file in resource.get_all_files():
            # Calculate the full file path with the resource as the root of the path.
            if resource.kind_name == 'project':
                # File path needs the project and storage names prepended to it.
                file_path = '/{}/{}/{}'.format(resource.title,
                                               file.provider, file.materialized_path)
            elif resource.kind_name == 'storage':
                # File path needs the storage name prepended to it.
                file_path = '/{}/{}'.format(file.provider, file.materialized_path)
            else: # elif project
                # File Path needs to start at the folder and strip everything before it.
                # Example: If the resource is 'Docs2' and the starting path is
                # '/Project/Storage/Docs1/Docs2/file.jpeg' then the final path
                # needs to be '/Docs2/file.jpeg'
                path_to_strip = resource.materialized_path[:-(len(resource.title)+2)]
                file_path = file.materialized_path[len(path_to_strip):]

            # Append the url and file data dictionary so we can asynchronously call all downloads.
            file_urls.append(file.download_url)
            file_data.append({'url': file.download_url, 'file': file, 'file_path': file_path})

        # Asynchronously make all download requests
        loop = asyncio.new_event_loop()
        download_data = loop.run_until_complete(async_main(file_urls, token))

        # Go through the data returned from the asynchronous calls and match it with the file_data
        # gathered earlier. Create dictionaries of data to send back to the view.
        for download in download_data:
            file_dict = get_dictionary_from_list(file_data, 'url', download['url'])
            files.append({
                'file': download['binary_content'],
                'hashes': file_dict['file'].hashes,
                'title': file_dict['file'].title,
                'path': file_dict['file_path']
            })
    return files