import asyncio
import base64
import aiohttp
import requests

from rest_framework import status

from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.targets.figshare.utilities.helpers.download_content import download_project, download_article
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


def figshare_download_resource(token, resource_id):
    """
    Fetch the requested resource from FigShare along with its hash information.

    Parameters
    ----------
    token : str
        User's FigShare token
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
        headers, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    split_id = str(resource_id).split(":")

    # But first we need to see whether it is a public project, or a private project.
    project_url = "https://api.figshare.com/v2/account/projects/{}".format(split_id[0])
    response = requests.get(project_url, headers=headers)
    if response.status_code != 200:
        project_url = "https://api.figshare.com/v2/projects/{}".format(split_id[0])
        response = requests.get(project_url, headers=headers)
        if response.status_code != 200:
            raise PresQTResponseException("The resource could not be found by the requesting user.",
                                          status.HTTP_404_NOT_FOUND)
    data = response.json()
    project_name = data['title']
    file_urls = None

    if len(split_id) == 1:
        # This will be a download of a whole project.
        articles_url = project_url + "/articles"
        files, empty_containers, action_metadata = download_project(
            username, articles_url, headers, project_name, [])
        file_urls = [file['file'] for file in files]

    elif len(split_id) == 2 or len(split_id) == 3:
        # We have an article or a file so we need to get the article url
        article_url = "https://api.figshare.com/v2/account/projects/{}/articles/{}".format(
            split_id[0], split_id[1])
        response = requests.get(article_url, headers=headers)

        if response.status_code != 200:
            # Let's see if this is a public article....
            article_url = "https://api.figshare.com/v2/articles/{}".format(split_id[1])
            response = requests.get(article_url, headers=headers)

            if response.status_code != 200:
                raise PresQTResponseException("The resource could not be found by the requesting user.",
                                              status.HTTP_404_NOT_FOUND)
        if len(split_id) == 2:
            files, empty_containers, action_metadata = download_article(
                username, article_url, headers, project_name, [])
            file_urls = [file['file'] for file in files]

        elif len(split_id) == 3:
            data = response.json()
            for file in data['files']:
                if str(file['id']) == split_id[2]:
                    files = [{
                        "file": requests.get(file['download_url'], headers=headers).content,
                        "hashes": {"md5": file['computed_md5']},
                        "title": file['name'],
                        "path": "/{}".format(file['name']),
                        "source_path": "/{}/{}/{}".format(project_name, data['title'], file['name']),
                        "extra_metadata": {"size": file['size']}
                    }]
                    empty_containers = []
                    action_metadata = {"sourceUsername": username}
            else:
                # We could not find the file.
                raise PresQTResponseException("The resource could not be found by the requesting user.",
                                              status.HTTP_404_NOT_FOUND)
    if file_urls:
        # Start the async calls for project or article downloads
        loop = asyncio.new_event_loop()
        download_data = loop.run_until_complete(async_main(file_urls, headers))

        # Go through the file dictionaries and replace the file path with the binary_content
        for file in files:
            file['file'] = get_dictionary_from_list(
                download_data, 'url', file['file'])['binary_content']

    return {
        'resources': files,
        'empty_containers': empty_containers,
        'action_metadata': action_metadata
    }
