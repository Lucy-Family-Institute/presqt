import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def validation_check(token):
    """
    Ensure a proper GitHub API token has been provided.

    Parameters
    ----------
    token : str
        User's GitHub token

    Returns
    -------
    The requesting user's username and properly formatted GitHub Auth header.
    """
    header = {"Authorization": "token {}".format(token)}
    validation = requests.get("https://api.github.com/user", headers=header).json()
    try:
        validation['login']
    except:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.', 
                                      status.HTTP_401_UNAUTHORIZED)

    return header
