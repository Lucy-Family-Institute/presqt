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
    Three lists of keywords.
    """
    try:
        enhanced_keywords = request.data['enhanced_keywords']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'enhanced_keywords' is missing from the request body.",
            status.HTTP_400_BAD_REQUEST)

    try:
        custom_keywords = request.data['custom_keywords']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'custom_keywords' is missing from the request body.",
            status.HTTP_400_BAD_REQUEST)

    if type(enhanced_keywords) is not list:
        raise PresQTValidationError(
            "PresQT Error: 'enhanced_keywords' must be in list format.",
            status.HTTP_400_BAD_REQUEST)
    elif type(custom_keywords) is not list:
        raise PresQTValidationError(
            "PresQT Error: 'custom_keywords' must be in list format.",
            status.HTTP_400_BAD_REQUEST)


    return enhanced_keywords, custom_keywords