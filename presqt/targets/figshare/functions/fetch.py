import requests
from rest_framework import status

from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.targets.figshare.utilities.get_figshare_project_data import (
    get_figshare_project_data, get_search_project_data)
from presqt.utilities import PresQTResponseException


def figshare_fetch_resources(token, query_parameter, process_info_path):
    """
    Fetch all users projects from FigShare.

    Parameters
    ----------
    token : str
        User's FigShare token
    query_parameter : dict
        The search parameter passed to the API View
        Gets passed formatted as {'title': 'search_info'}
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    List of dictionary objects that represent FigShare resources.
    Dictionary must be in the following format:
        {
            "kind": "container",
            "kind_name": "folder",
            "id": "12345",
            "container": "None",
            "title": "Folder Name",
        }
    We are also returning a dictionary of pagination information.
    Dictionary must be in the following format:
        {
            "first_page": '1',
            "previous_page": None,
            "next_page": None,
            "last_page": '1',
            "total_pages": '1',
            "per_page": 10
        }
    """
    base_url = "https://api.figshare.com/v2/"

    try:
        headers, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    pages = {
        "first_page": '1',
        "previous_page": None,
        "next_page": None,
        "last_page": '1',
        "total_pages": '1',
        "per_page": 10}

    if query_parameter and 'page' not in query_parameter:
        if 'id' in query_parameter:
            response = requests.get("{}projects/{}".format(base_url, query_parameter['id']))
            if response.status_code != 200:
                raise PresQTResponseException("Project with id, {}, can not be found.".format(query_parameter['id']),
                                              status.HTTP_404_NOT_FOUND)
        return get_search_project_data(response.json(), headers, [], process_info_path), pages

    else:
        if query_parameter and 'page' in query_parameter:
            url = "{}account/projects?page={}".format(base_url, query_parameter['page'])
        else:
            url = "{}account/projects?page=1".format(base_url)

        response_data = requests.get(url, headers=headers).json()

    return get_figshare_project_data(response_data, headers, [], process_info_path), pages


def figshare_fetch_resource(token, resource_id):
    """
    Fetch the FigShare resource matching the resource_id given.

    Parameters
    ----------
    token : str
        User's FigShare token

    resource_id : str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the FigShare resource.
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
    try:
        headers, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    split_id = str(resource_id).split(':')

    if len(split_id) == 1:
        # This is a top level project
        project_url = "https://api.figshare.com/v2/account/projects/{}".format(resource_id)
        response = requests.get(project_url, headers=headers)

        if response.status_code != 200:
            # Let's see if this is a public project....
            project_url = "https://api.figshare.com/v2/projects/{}".format(resource_id)
            response = requests.get(project_url, headers=headers)

            if response.status_code != 200:
                raise PresQTResponseException("The resource could not be found by the requesting user.",
                                              status.HTTP_404_NOT_FOUND)
        data = response.json()
        return {
            "kind": "container",
            "kind_name": "project",
            "id": data["id"],
            "title": data['title'],
            "date_created": data['created_date'],
            "date_modified": data['modified_date'],
            "hashes": {},
            "extra": {
                "funding": data['funding'],
                "collaborators": data['collaborators'],
                "description": data['description'],
                "custom_fields": data['custom_fields']
            }}

    elif len(split_id) == 2:
        # This is an article
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
        data = response.json()
        extra = {}
        for key, value in data.items():
            if key not in ['id', 'title', 'created_date', 'modified_date']:
                extra[key] = value

        return {
            "kind": "container",
            "kind_name": data['defined_type_name'],
            "id": resource_id,
            "title": data['title'],
            "date_created": data['created_date'],
            "date_modified": data['modified_date'],
            "hashes": {},
            "extra": extra}

    elif len(split_id) == 3:
        # This is a file
        # Check the article it belongs to to get the file info....
        article_url = "https://api.figshare.com/v2/account/projects/{}/articles/{}".format(
            split_id[0], split_id[1])
        response = requests.get(article_url, headers=headers)

        if response.status_code != 200:
            # Let's see if this file belongs to a public article....
            article_url = "https://api.figshare.com/v2/articles/{}".format(split_id[1])
            response = requests.get(article_url, headers=headers)

            if response.status_code != 200:
                raise PresQTResponseException("The resource could not be found by the requesting user.",
                                              status.HTTP_404_NOT_FOUND)
        for file in response.json()['files']:
            if str(file['id']) == split_id[2]:
                return {
                    "kind": "item",
                    "kind_name": "file",
                    "id": resource_id,
                    "title": file['name'],
                    "date_created": None,
                    "date_modified": None,
                    "hashes": {
                        "md5": file['computed_md5']
                    },
                    "extra": {
                        "size": file['size']
                    }
                }
        else:
            raise PresQTResponseException("The resource could not be found by the requesting user.",
                                          status.HTTP_404_NOT_FOUND)
