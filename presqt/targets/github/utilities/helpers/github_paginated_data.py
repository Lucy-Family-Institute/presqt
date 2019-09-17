import requests

from presqt.targets.github.utilities import get_page_total


def github_paginated_data(username, header):
    """
    """
    base_url = "https://api.github.com/users/{}/repos".format(username)
    data = requests.get(base_url, headers=header).json()
    page_total = get_page_total(username, header)
    # We want to start building urls from page 2 as we already have the data from page 1.
    page_count = 2
    while page_count <= page_total:
        more_url = (base_url + '?page={}'.format(page_count))
        more_data = requests.get(more_url, headers=header).json()
        data.extend(more_data)
        page_count += 1

    return data
