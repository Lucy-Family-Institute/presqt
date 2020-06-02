from rest_framework import status

from presqt.utilities import PresQTValidationError


def keyword_action_validation(request):
    try:
        keyword_action = request.META['HTTP_PRESQT_KEYWORD_ACTION']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'presqt-keyword-action' missing in the request headers.",
            status.HTTP_400_BAD_REQUEST)

    if keyword_action not in ['automatic', 'manual']:
        raise PresQTValidationError(
            "PresQT Error: '{}' is not a valid keyword_action. "
            "The options are 'automatic' or 'manual'.".format(keyword_action),
            status.HTTP_400_BAD_REQUEST)

    return keyword_action