import requests

from rest_framework import status

from presqt.utilities import PresQTValidationError


def zenodo_validation_check(token):
    """
    Ensure a proper Zenodo API token has been provided.

    Parameters
    ----------
    token : str
        User's Zenodo token

    Returns
    -------
    Properly formatted Zenodo Auth parameter.
    """

    auth_parameter = {'access_token': token}

    # Gonna use the test server for now
    validator = requests.get("https://zenodo.org/api/deposit/depositions",
                             params=auth_parameter).status_code

    if validator != 200:
        raise PresQTValidationError("Token is invalid. Response returned a 401 status code.",
                                    status.HTTP_401_UNAUTHORIZED)

    return auth_parameter
