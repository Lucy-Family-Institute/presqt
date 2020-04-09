import requests
from rest_framework import status

from presqt.targets.gitlab.utilities.gitlab_paginated_data import gitlab_paginated_data
from presqt.targets.gitlab.utilities.validation_check import validation_check
from presqt.utilities import PresQTResponseException


def gitlab_fetch_resources(token, search_parameter):
    """
    Fetch all users projects from GitLab.

    Parameters
    ----------
    token : str
        User's GitLab token
    search_parameter : dict
        The search parameter passed to the API View
        Gets passed formatted as {'title': 'search_info'}

    Returns
    -------
    List of dictionary objects that represent GitLab resources.
    Dictionary must be in the following format:
        {
            "kind": "container",
            "kind_name": "folder",
            "id": "12345",
            "container": "None",
            "title": "Folder Name",
        }
    """
    base_url = "https://gitlab.com/api/v4/"
    try:
        headers, user_id = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    if search_parameter:
        if 'author' in search_parameter:
            author_url = "{}users?username={}".format(base_url, search_parameter['author'])
            author_response_json = requests.get(author_url, headers=headers).json()
            if not author_response_json:
                return []
            data = requests.get(
                "https://gitlab.com/api/v4/users/{}/projects".format(author_response_json[0]['id']), headers=headers).json()

        elif 'general' in search_parameter:
            search_url = "{}search?scope=projects&search={}".format(
                base_url, search_parameter['general'])
            data = requests.get(search_url, headers=headers).json()

        elif 'id' in search_parameter:
            project_url = "{}projects/{}".format(base_url, search_parameter['id'])
            project_response = requests.get(project_url, headers=headers)

            if project_response.status_code == 404:
                return []
            data_json = project_response.json()
            return [{
                "kind": "container",
                "kind_name": "project",
                "container": None,
                "id": data_json['id'],
                "title": data_json['name']}]

        elif 'title' in search_parameter:
            title_url = "{}/projects?search={}".format(base_url, search_parameter['title'])
            data = requests.get(title_url, headers=headers).json()

    else:
        data = gitlab_paginated_data(headers, user_id)

    resources = []
    for project in data:
        # We are not going to display projects that the user has deleted. Gitlab does not have
        # immediate deletion, instead they hold onto projects for a week before removal.
        # Also of note, Private Projects do not have this same key, which is why we need the `or`
        if ('marked_for_deletion_at' in project.keys() and not project['marked_for_deletion_at']) or (
                'marked_for_deletion_at' not in project.keys()):
            resource = {
                "kind": "container",
                "kind_name": "project",
                "container": None,
                "id": project["id"],
                "title": project["name"]}
            resources.append(resource)
    return resources


def gitlab_fetch_resource(token, resource_id):
    """
    Fetch the GitLab resource matching the resource_id given.

    Parameters
    ----------
    token : str
        User's GitLab token

    resource_id : str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the GitLab resource.
    Dictionary must be in the following format:
    {
        "kind": "container",
        "kind_name": "project",
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
    project_url = "https://gitlab.com/api/v4/projects/{}".format(resource_id)

    try:
        headers, user_id = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    response = requests.get(project_url, headers=headers)

    if response.status_code != 200:
        raise PresQTResponseException("The resource could not be found by the requesting user.",
                                      status.HTTP_404_NOT_FOUND)

    data = response.json()

    resource = {
        "kind": "container",
        "kind_name": "project",
        "id": data['id'],
        "title": data['name'],
        "date_created": data['created_at'],
        "date_modified": data['last_activity_at'],
        "hashes": {},
        "extra": {}
    }
    for key, value in data.items():
        if '_url' in key:
            pass
        else:
            resource['extra'][key] = value

    return resource
