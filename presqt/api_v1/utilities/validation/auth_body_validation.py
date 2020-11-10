from rest_framework import status

from presqt.utilities import PresQTValidationError


def auth_body_validation(request):
    """
    Extract authorization from the request body.

    Parameters
    ----------
    request: HTTP Request Object

    Returns
    -------
    authorization:
        Authorization token for the target.
    """
    request_data = request.data

    try:
        authorization = request_data['authorization']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: authorization was not found in the request body.", status.HTTP_400_BAD_REQUEST)

    return authorization
