import requests

from rest_framework import status

from presqt.targets.github.utilities import validation_check, github_paginated_data
from presqt.targets.github.utilities.helpers.github_file_data import get_github_repository_data
from presqt.targets.github.utilities.helpers.get_page_numbers import get_page_numbers
from presqt.utilities import PresQTResponseException


def github_fetch_resources(token, query_parameter):
    """
    Fetch all users resources from GitHub.

    Parameters
    ----------
    token : str
        User's GitHub token
    query_parameter : dict
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
    We are also returning a dictionary of pagination information.
    Dictionary must be in the following format:
        {
            "first_page": '1',
            "previous_page": None,
            "next_page": None,
            "last_page": '1',
            "total_pages": '1',
            "per_page": 30
        }
    """
    try:
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    header['Accept'] = 'application/vnd.github.mercy-preview+json'

    pages = {
        "first_page": '1',
        "previous_page": None,
        "next_page": None,
        "last_page": '1',
        "total_pages": '1',
        "per_page": 30}

    if query_parameter:
        if 'author' in query_parameter:
            search_url = "https://api.github.com/users/{}/repos".format(query_parameter['author'])
            initial_data = requests.get(search_url, headers=header)
            if initial_data.status_code != 200:
                return []
            data = initial_data.json()

        elif 'general' in query_parameter:
            search_url = "https://api.github.com/search/repositories?q={}".format(
                query_parameter['general'])
            data = requests.get(search_url, headers=header).json()['items']

        elif 'id' in query_parameter:
            query_parameters = query_parameter['id']
            search_url = "https://api.github.com/repositories/{}".format(query_parameters)
            data = requests.get(search_url, headers=header)
            if data.status_code != 200:
                return []
            data = [data.json()]

        elif 'title' in query_parameter:
            query_parameters = query_parameter['title'].replace(' ', '+')
            search_url = "https://api.github.com/search/repositories?q={}+in:name+sort:updated".format(
                query_parameters)
            data = requests.get(search_url, headers=header).json()['items']

        elif 'keywords' in query_parameter:
            query_parameters = query_parameter['keywords'].replace(' ', '+')
            search_url = "https://api.github.com/search/repositories?q={}+in:topics+sort:updated".format(
                query_parameters)
            data = requests.get(search_url, headers=header).json()['items']

        elif 'page' in query_parameter:
            data = github_paginated_data(token, query_parameter['page'])
            pages = get_page_numbers(
                "https://api.github.com/user/repos?page={}".format(query_parameter['page']),
                header, query_parameter['page'])

    else:
        data = github_paginated_data(token, '1')
        pages = get_page_numbers("https://api.github.com/user/repos?page=1", header, '1')

    return get_github_repository_data(data, header, []), pages


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

    header['Accept'] = 'application/vnd.github.mercy-preview+json'

    # Without a colon, we know this is a top level repo
    if ':' not in str(resource_id):
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
    # If there is a colon in the resource id, the resource could be a directory or a file
    else:
        resource_id = resource_id.replace('%2F', '%252F').replace('%2E', '%252E')
        partitioned_id = resource_id.partition(':')
        repo_id = partitioned_id[0]
        path_to_resource = partitioned_id[2].replace(
            '%252F', '/').replace('%252E', '.').replace('%28', '(').replace('%29', ')')
        # This initial request will get the repository, which we need to get the proper contents url
        # The contents url contains a username and project name which we don't have readily available
        # to us.
        initial_repo_get = requests.get('https://api.github.com/repositories/{}'.format(repo_id), headers=header)
        repo_data = initial_repo_get.json()
        if initial_repo_get.status_code != 200:
            raise PresQTResponseException("The resource could not be found by the requesting user.",
                                          status.HTTP_404_NOT_FOUND)

        get_url = '{}{}'.format(repo_data['contents_url'].partition('{')[0], path_to_resource)
        file_get = requests.get(get_url, headers=header)
        file_json = file_get.json()
        if file_get.status_code == 403:
            # 403 most likely means the blob contents were too big so we have to attempt to
            # get the file contents a different method
            trees_url = '{}/master?recursive=1'.format(repo_data['trees_url'][:-6])
            trees_response = requests.get(trees_url, headers=header)
            for tree in trees_response.json()['tree']:
                if path_to_resource == tree['path']:
                    file_sha = tree['sha']
            git_blob_url = 'https://api.github.com/repos/{}/git/blobs/{}'.format(repo_data['full_name'], file_sha)
            file_get = requests.get(git_blob_url, headers=header)
            file_json = file_get.json()
            file_json['name'] = path_to_resource.rpartition('/')[2]
            file_json['path'] = path_to_resource.rpartition('/')
        elif file_get.status_code != 200:
            raise PresQTResponseException("The resource could not be found by the requesting user.",
                                          status.HTTP_404_NOT_FOUND)

        if isinstance(file_json, list):
            return {
                "kind": "container",
                "kind_name": "dir",
                "id": resource_id,
                "title": path_to_resource.rpartition('/')[2],
                "date_created": None,
                "date_modified": None,
                "hashes": {},
                "extra": {}
            }

        else:
            return {
                "kind": "item",
                "kind_name": "file",
                "id": resource_id,
                "title": file_json['name'],
                "date_created": None,
                "date_modified": None,
                "hashes": {},
                "extra": {'size': file_json['size'],
                          'commit_hash': file_json['sha'],
                          'path': file_json['path']}
            }
