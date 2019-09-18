import math
import requests


def get_page_total(token):
    """
    Get the total number of project pages based on the GitHub username.

    Parameters
    ----------
    token : str
        The user's GitHub Auth token.

    Returns
    -------
    The number of pages of repos the user has.
    """
    user_url = 'https://api.github.com/user?access_token={}'.format(token)
    user_data = requests.get(user_url, headers=header).json()
    public_repos = user_data['public_repos']
    private_repos = user_data['total_private_repos']
    total_repos = public_repos + private_repos
    page_total = math.ceil(total_repos/29)

    return page_total
