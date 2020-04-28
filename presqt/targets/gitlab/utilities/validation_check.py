import requests
from rest_framework import status

from presqt.utilities import PresQTResponseException


def validation_check(token):
    """
    Ensure a proper GitLab API token has been provided.

    Parameters
    ----------
    token : str
        User's GitLab token

    Returns
    -------
    The requesting user's username and properly formatted GitLab Auth header.
    """
    headers = {"Private-Token": "{}".format(token)}
    request = requests.get("https://gitlab.com/api/v4/user", headers=headers)

    if request.status_code == 401:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    else:
        return headers, request.json()['id']