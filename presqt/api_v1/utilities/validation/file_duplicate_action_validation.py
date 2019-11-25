from rest_framework import status

from presqt.utilities import PresQTValidationError


def file_duplicate_action_validation(request):
    try:
        file_duplicate_action = request.META['HTTP_PRESQT_FILE_DUPLICATE_ACTION']
    except KeyError:
        raise PresQTValidationError(
            "'presqt-file-duplicate-action' missing in the request headers.",
            status.HTTP_400_BAD_REQUEST)

    if file_duplicate_action not in ['ignore', 'update']:
        raise PresQTValidationError(
            "'{}' is not a valid file_duplicate_action. "
            "The options are 'ignore' or 'update'.".format(file_duplicate_action),
            status.HTTP_400_BAD_REQUEST)

    return file_duplicate_action