import asyncio
import aiohttp
import requests

from rest_framework import status

from presqt.targets.curate_nd.utilities import get_curate_nd_resource
from presqt.targets.curate_nd.classes.main import CurateND
from presqt.utilities import PresQTInvalidTokenError, PresQTResponseException

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
        User's OSF token

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, token) for url in url_list])


def curate_nd_download_resource(token, resource_id):
    """
    """
    try:
        curate_instance = CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
            status.HTTP_401_UNAUTHORIZED)

    # Get the resource
    resource = get_curate_nd_resource(resource_id, curate_instance)

    # Get all the files for the provided resources.
    files = []
    empty_containers = []
    if resource.kind_name == 'file':
        binary_file = resource.download()
        files.append({
            'file': binary_file,
            'hashes': {'md5': resource.md5},
            'title': resource.title,
            # If the file is the only resource we are downloading then we don't need it's full path.
            'path': '/{}'.format(resource.title)})
    else:
        if not resource.extra['containedFiles']:
            empty_containers.append('{}'.format(resource.title))
        else:
            title_helper = {}
            file_urls = []
            for file in resource.extra['containedFiles']:
                title_helper[file['downloadUrl']] = file['label']
                file_urls.append(file['downloadUrl'])
            loop = asyncio.new_event_loop()
            download_data = loop.run_until_complete(async_main(file_urls, token))

            for file in download_data:
                files.append({
                    'file': file['binary_content'],
                    'hashes': {'md5': file['md5']},
                    'title': title_helper[file['url']],
                    'path': '/{}/{}'.format(resource.title, title_helper[file['url']])})

    return files, empty_containers
