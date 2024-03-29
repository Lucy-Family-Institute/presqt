import requests
from rest_framework import status

from presqt.targets.gitlab.utilities.gitlab_paginated_data import gitlab_paginated_data
from presqt.targets.gitlab.utilities.validation_check import validation_check
from presqt.targets.gitlab.utilities.get_gitlab_project_data import get_gitlab_project_data
from presqt.targets.gitlab.utilities.get_page_numbers import get_page_numbers
from presqt.targets.gitlab.utilities.gitlab_get_children import gitlab_get_children
from presqt.utilities import PresQTResponseException


def gitlab_fetch_resources(token, query_parameter):
    """
    Fetch all users projects from GitLab.

    Parameters
    ----------
    token : str
        User's GitLab token
    query_parameter : dict
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
    We are also returning a dictionary of pagination information.
    Dictionary must be in the following format:
        {
            "first_page": '1',
            "previous_page": None,
            "next_page": None,
            "last_page": '1',
            "total_pages": '1',
            "per_page": 20
        }
    """
    base_url = "https://gitlab.com/api/v4/"
    try:
        headers, user_id = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    pages = {
        "first_page": '1',
        "previous_page": None,
        "next_page": None,
        "last_page": '1',
        "total_pages": '1',
        "per_page": 20}

    # If there's only one query parameter and the key is page
    if len(query_parameter.keys()) == 1 and 'page' in query_parameter:
        data = gitlab_paginated_data(headers, user_id, page_number=query_parameter['page'])
        pages = get_page_numbers(
            "https://gitlab.com/api/v4/users/{}/projects".format(user_id), headers)
    else:
        if not query_parameter:
            data = gitlab_paginated_data(headers, user_id, page_number='1')
            pages = get_page_numbers(
                "https://gitlab.com/api/v4/users/{}/projects".format(user_id), headers)
        else:
            if 'author' in query_parameter:
                author_url = "{}users?username={}".format(base_url, query_parameter['author'])
                author_response_json = requests.get(author_url, headers=headers).json()
                if not author_response_json:
                    return [], pages
                url = "https://gitlab.com/api/v4/users/{}/projects".format(
                    author_response_json[0]['id'])
                if 'page' in query_parameter:
                    url = "https://gitlab.com/api/v4/users/{}/projects?page={}".format(
                        author_response_json[0]['id'], query_parameter['page'])

            elif 'general' in query_parameter:
                url = "{}/projects?search={}".format(
                    base_url, query_parameter['general'])

            elif 'id' in query_parameter:
                project_url = "{}projects/{}".format(base_url, query_parameter['id'])
                project_response = requests.get(project_url, headers=headers)

                if project_response.status_code == 404:
                    return [], pages
                return get_gitlab_project_data([project_response.json()], headers, []), pages

            elif 'title' in query_parameter:
                url = "{}/projects?search={}".format(base_url, query_parameter['title'])

            if 'page' in query_parameter and 'page' not in url:
                url = '{}&page={}'.format(url, query_parameter['page'])

            data = requests.get(url, headers=headers).json()
            pages = get_page_numbers(url, headers)

    return get_gitlab_project_data(data, headers, []), pages


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
    try:
        headers, user_id = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    partitioned_id = str(resource_id).partition(':')

    if ':' in str(resource_id):
        project_id = partitioned_id[0]
        project_url = "https://gitlab.com/api/v4/projects/{}".format(project_id)

        response = requests.get(project_url, headers=headers)
        if response.status_code != 200:
            raise PresQTResponseException("The resource could not be found by the requesting user.",
                                          status.HTTP_404_NOT_FOUND)
        path_to_resource = partitioned_id[2].replace(
            '%252F', '%2F').replace('%252E', '%2E').replace('+', ' ')
        string_path_to_resource = path_to_resource.replace('%2F', '/').replace('%2E', '.')

        # Figure out the resource type (file, folder)
        tree_url = 'https://gitlab.com/api/v4/projects/{}/repository/tree?recursive=1'.format(
            project_id)
        file_data = gitlab_paginated_data(headers, None, tree_url)
        resource_type = 'folder'
        for data in file_data:
            if data['path'] == string_path_to_resource:
                if data['type'] == 'blob':
                    resource_type = 'file'

        # Resource is a file
        if resource_type == 'file':
            response = requests.get(
                'https://gitlab.com/api/v4/projects/{}/repository/files/{}?ref=master'.format(
                    project_id, path_to_resource), headers=headers)

            data = response.json()
            resource = {
                "kind": "item",
                "kind_name": "file",
                "id": resource_id,
                "identifier": None,
                "title": data['file_name'],
                "date_created": None,
                "date_modified": None,
                "hashes": {'sha256': data['content_sha256']},
                "extra": {'ref': data['ref'], 'commit_id': data['commit_id'], 'size': data['size']},
                "children": []}

        # Resource is a folder
        else:
            response = requests.get(
                'https://gitlab.com/api/v4/projects/{}/repository/tree?path={}'.format(
                    project_id, path_to_resource), headers=headers)
            # If the directory doesn't exist, they return an empty list
            if response.json() == []:
                raise PresQTResponseException("The resource could not be found by the requesting user.",
                                              status.HTTP_404_NOT_FOUND)
            children = gitlab_get_children(response.json(), resource_id, project_id)
            resource = {
                "kind": "container",
                "kind_name": "dir",
                "id": resource_id,
                "identifier": None,
                "title": path_to_resource.rpartition('%2F')[2].replace('%2E', '.'),
                "date_created": None,
                "date_modified": None,
                "hashes": {},
                "extra": {},
                "children": children}

    # This is the top level project
    else:
        project_url = "https://gitlab.com/api/v4/projects/{}".format(resource_id)

        response = requests.get(project_url, headers=headers)
        if response.status_code != 200:
            raise PresQTResponseException("The resource could not be found by the requesting user.",
                                          status.HTTP_404_NOT_FOUND)

        data = response.json()
        children_data = requests.get("{}/repository/tree".format(project_url), headers=headers).json()

        # ERROR, return no children
        if children_data == [] or 'message' in children_data:
            children = []
        else:
            children = gitlab_get_children(children_data, resource_id, resource_id)

        resource = {
            "kind": "container",
            "kind_name": "project",
            "id": data['id'],
            "identifier": data['web_url'],
            "title": data['name'],
            "date_created": data['created_at'],
            "date_modified": data['last_activity_at'],
            "hashes": {},
            "extra": {},
            "children": children
        }
        for key, value in data.items():
            if '_url' in key:
                pass
            else:
                resource['extra'][key] = value

    return resource
