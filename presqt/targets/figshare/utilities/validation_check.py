import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def validation_check(token):
    """
    Ensure a proper FigShare API token has been provided.

    Parameters
    ----------
    token : str
        User's FigShare token

    Returns
    -------
    The properly formatted FigShare Auth header.
    """

    headers = {"Authorization": "token {}".format(token)}
    request = requests.get("http://api.figshare.com/v2/account", headers=headers)

    if request.status_code == 403:
        raise PresQTResponseException("Token is invalid. Response returned a 403 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    username = request.json()['email']

    return headers, username
