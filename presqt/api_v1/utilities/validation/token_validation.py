from rest_framework import status

from presqt.exceptions import PresQTAuthorizationError


def token_validation(request):
    """
    Perform token validation.

    Parameters
    ----------
    request : HTTP request object

    Returns
    -------
    Returns the token if the validation is successful.
    Raises a custom AuthorizationException error if the validation fails.
    """
    # Validate that the proper token exists in the request.
    try:
        return request.META['HTTP_PRESQT_SOURCE_TOKEN']
    except KeyError:
        raise PresQTAuthorizationError(
            "'presqt-source-token' missing in the request headers.",
            status.HTTP_400_BAD_REQUEST)