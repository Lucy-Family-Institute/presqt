import requests

from rest_framework import status

from presqt.targets.github.utilities import get_page_total, validation_check, github_paginated_data
from presqt.utilities import PresQTResponseException


def github_fetch_resources(token):
    """
    Fetch all users repos from GitHub.

    Parameters
    ----------
    token : str
        User's GitHub token

    Returns
    -------
    List of dictionary objects that represent GitHub resources.
    Dictionary must be in the following format:
        {
            "kind": "container",
            "kind_name": "folder",
            "id": "12345",
            "container": "None",
            "title": "Folder Name",
        }
    See https://app.gitbook.com/@crc-nd/s/presqt/project-description/developer-documentation/code-documentation/resources for details.
    """
    try:
        username, header = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.', 
                                      status.HTTP_401_UNAUTHORIZED)

    data = github_paginated_data(username, header)

    resources = []

    for repo in data:
        resource = {
            "kind": "container",
            "kind_name": "repo",
            "container": None,
            "id": repo["id"],
            "title": repo["name"]}
        resources.append(resource)

    return resources


def github_fetch_resource(token, resource_id):
    """
    Fetch the GitHub resource matching the resource_id given.

    Parameters
    ----------
    token : str
        User's GitHub token

    resource_id : str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the GitHub resource.
    Dictionary must be in the following format:
    {
        "kind": "container",
        "kind_name": "repo",
        "id": "12345",
        "title": "23296359282_934200ec59_o.jpg",
        "date_created": "2019-05-13T14:54:17.129170Z",
        "date_modified": "2019-05-13T14:54:17.129170Z",
        "hashes": {
            "md5": "aaca7ef067dcab7cb8d79c36243823e4",
        },
        "extra": {
            "any": extra,
            "values": here
        }
    }
    """
    try:
        username, header = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.',
                                      status.HTTP_401_UNAUTHORIZED)

    data = github_paginated_data(username, header)

    resource = {}
    for entry in data:
        if entry['id'] == int(resource_id):
            resource['kind'] = 'container'
            resource['kind_name'] = 'repo'
            resource['id'] = entry['id']
            resource['title'] = entry['name']
            resource['date_created'] = entry['created_at']
            resource['date_modified'] = entry['updated_at']
            resource['hashes'] = {"sha256": None}
            resource['extra'] = {}
            for key, value in entry.items():
                if '_url' in key:
                    pass
                else:
                    resource['extra'][key] = value
            break

    return resource
