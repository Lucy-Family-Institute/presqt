import requests


def gitlab_paginated_data(headers, user_id):
    """
    For the given user, find and return all project data.

    Parameters
    ----------
    headers : dict
        Headers for requests.
    user_id: str
        ID of the GitLab user.

    Returns
    -------
    List of all paginated data.
    """
    project_url = "https://gitlab.com/api/v4/users/{}/projects".format(user_id)

    data = []
    response = requests.get(project_url, headers=headers)
    next_page_number = response.headers['X-Next-Page']
    data.extend(response.json())

    while next_page_number:
        next_url = "{}?page={}".format(project_url, next_page_number)
        next_response = requests.get(next_url, headers=headers)
        data.extend(next_response.json())
        next_page_number = next_response.headers['X-Next-Page']

    return data
