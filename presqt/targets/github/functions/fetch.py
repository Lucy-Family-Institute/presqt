import re
import requests

from rest_framework import status

from presqt.targets.github.utilities import validation_check, github_paginated_data
from presqt.utilities import PresQTResponseException


def github_fetch_resources(token, search_parameter):
    """
    Fetch all users repos from GitHub.

    Parameters
    ----------
    token : str
        User's GitHub token
    search_parameter : dict
        The search parameter passed to the API View
        Gets passed formatted as {'title': 'search_info'}

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
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    if search_parameter:
        if 'title' in search_parameter:
            search_parameters = search_parameter['title'].replace(' ', '+')
            search_url = "https://api.github.com/search/repositories?q={}+in:name+sort:updated".format(
                search_parameters)
            data = requests.get(search_url, headers=header).json()['items']

        elif 'id' in search_parameter:
            search_parameters = search_parameter['id']
            search_url = "https://api.github.com/repositories/{}".format(search_parameters)
            data = requests.get(search_url, headers=header)
            if data.status_code != 200:
                return []
            data_json = data.json()
            return [{
                "kind": "container",
                "kind_name": "repo",
                "container": None,
                "id": data_json['id'],
                "title": data_json['name']}]

        elif 'author' in search_parameter:
            search_url = "https://api.github.com/users/{}/repos".format(search_parameter['author'])
            initial_data = requests.get(search_url, headers=header)
            if initial_data.status_code != 200:
                return []
            data = initial_data.json()
    else:
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
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    project_url = 'https://api.github.com/repositories/{}'.format(resource_id)

    response = requests.get(project_url, headers=header)

    if response.status_code != 200:
        raise PresQTResponseException("The resource could not be found by the requesting user.",
                                      status.HTTP_404_NOT_FOUND)

    data = response.json()

    resource = {
        "kind": "container",
        "kind_name": "repo",
        "id": data['id'],
        "title": data['name'],
        "date_created": data['created_at'],
        "date_modified": data['updated_at'],
        "hashes": {},
        "extra": {}
    }
    for key, value in data.items():
        if '_url' in key:
            pass
        else:
            resource['extra'][key] = value

    return resource
