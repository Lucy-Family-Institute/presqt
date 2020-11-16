from rest_framework import status

from presqt.utilities import PresQTValidationError


def get_source_token(request):
    """
    Perform token validation for the presqt-source-token header.

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
        raise PresQTValidationError(
            "PresQT Error: 'presqt-source-token' missing in the request headers.",
            status.HTTP_400_BAD_REQUEST)


def get_destination_token(request):
    """
    Perform token validation for the presqt-destination-token header.

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
        return request.META['HTTP_PRESQT_DESTINATION_TOKEN']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'presqt-destination-token' missing in the request headers.",
            status.HTTP_400_BAD_REQUEST)
