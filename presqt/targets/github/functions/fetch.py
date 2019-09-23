import requests

from rest_framework import status

from presqt.targets.github.utilities import validation_check, github_paginated_data
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
    """
    try:
        validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.',
                                      status.HTTP_401_UNAUTHORIZED)

    data = github_paginated_data(token)

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
        validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.',
                                      status.HTTP_401_UNAUTHORIZED)

    data = github_paginated_data(token)

    resource = {}
    for entry in data:
        if entry['id'] == int(resource_id):
            resource = {
                "kind": "container",
                "kind_name": "repo",
                "id": entry['id'],
                "title": entry['name'],
                "date_created": entry['created_at'],
                "date_modified": entry['updated_at'],
                "hashes": {},
                "extra": {}
            }
            for key, value in entry.items():
                if '_url' in key:
                    pass
                else:
                    resource['extra'][key] = value
            break
    else:
        resource = {}

    if resource == {}:
        raise PresQTResponseException("The resource could not be found by the requesting user.",
                                      status.HTTP_404_NOT_FOUND)

    return resource
