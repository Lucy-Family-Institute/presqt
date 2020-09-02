import requests

from presqt.utilities import PresQTInvalidTokenError


def validate_token(token):
    # Verify that the token provided is a valid one.
    response = requests.get('https://api.osf.io/v2/users/me/',
                            headers={'Authorization': 'Bearer {}'.format(token)})
    if response.status_code == 401:
        raise PresQTInvalidTokenError(
            "Token is invalid. Response returned a 401 status code.")