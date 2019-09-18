import math
import requests


def get_page_total(github_username, header):
    """
    Get the total number of project pages based on the GitHub username.

    Parameters
    ----------
    github_username : str
        The user's GitHub username.
    header : dict
        The GitHub Authorization header.

    Returns
    -------
    The number of pages of repos the user has.
    """
    user_url = 'https://api.github.com/users/{}'.format(github_username)
    total_repos = requests.get(user_url, headers=header).json()['public_repos']
    page_total = math.ceil(total_repos/29)

    return page_total
