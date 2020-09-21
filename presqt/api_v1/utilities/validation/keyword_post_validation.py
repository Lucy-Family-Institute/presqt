from rest_framework import status

from presqt.utilities import PresQTValidationError


def keyword_post_validation(request):
    """
    Validate that the correct keyword lists are in the POST body.

    Parameters
    ----------
    request: POST request

    Returns
    -------
    The list of keywords.
    """
    try:
        keywords = request.data['keywords']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'keywords' is missing from the request body.",
            status.HTTP_400_BAD_REQUEST)

    if type(keywords) is not list:
        raise PresQTValidationError(
            "PresQT Error: 'keywords' must be in list format.",
            status.HTTP_400_BAD_REQUEST)

    return keywords