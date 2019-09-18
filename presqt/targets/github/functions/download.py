import requests

from presqt.targets.github.utilities import (
    get_page_total, validation_check, github_paginated_data, download_content)
from presqt.utilities import PresQTInvalidTokenError, PresQTValidationError, PresQTResponseException


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

    data = github_paginated_data(username, header)

    for entry in data:
        if entry['id'] == int(resource_id):
            repo_name = entry['name']
            break
    # Get initial data from first page of data
    initial_url = "https://api.github.com/repos/{}/{}/contents".format(username, repo_name)
    files, empty_containers = download_content(initial_url, header, repo_name, [])

    return files, empty_containers
