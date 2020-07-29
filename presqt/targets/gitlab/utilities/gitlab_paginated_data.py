import requests


def gitlab_paginated_data(headers, user_id, url=None, page_number=None):
    """
    For the given user, find and return all project data.

    Parameters
    ----------
    headers : dict
        Headers for requests.
    user_id: str
        ID of the GitLab user.
    url: str
        URL to call
    page_number : str
        Used for GitLab pagination on resource_collection

    Returns
    -------
    List of all paginated data.
    """
    if not url:
        url = "https://gitlab.com/api/v4/users/{}/projects".format(user_id)

    data = []
    if page_number:
        response = requests.get("{}?page={}".format(url, page_number), headers=headers)
        if response.status_code != 200:
            return data
        data.extend(response.json())
        print(response.headers)
    else:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return data
        next_page_number = response.headers['X-Next-Page']
        data.extend(response.json())

        while next_page_number:
            if 'users' in url:
                next_url = "{}?page={}".format(url, next_page_number)
            else:
                next_url = "{}&page={}".format(url, next_page_number)
            next_response = requests.get(next_url, headers=headers)
            data.extend(next_response.json())
            next_page_number = next_response.headers['X-Next-Page']

    return data
