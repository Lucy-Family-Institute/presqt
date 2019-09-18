import requests

from presqt.targets.github.utilities import get_page_total


def github_paginated_data(username, token, header):
    """
    For the given user, find and return all repo data.

    Parameters
    ----------
    username : str
        The user's GitHub username
    token : str
        The user's GitHub token.
    header : dict
        The GitHub Authorization header

    Returns
    -------
    All paginated data.
    """
    base_url = "https://api.github.com/user/repos?access_token={}".format(token)
    data = requests.get(base_url).json()
    page_total = get_page_total(username, header)
    # We want to start building urls from page 2 as we already have the data from page 1.
    page_count = 2
    while page_count <= page_total:
        more_url = ("https://api.github.com/user/repos?page={}&access_token={}".format(page_count,
                                                                                       token))
        more_data = requests.get(more_url, headers=header).json()
        data.extend(more_data)
        page_count += 1

    return data
