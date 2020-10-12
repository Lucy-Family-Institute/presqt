from rest_framework import status

from presqt.utilities import PresQTValidationError


def fairshare_evaluator_validation(request):
    """
    Perform fairshare evaluator validation for the presqt-fairshare-evaluator-opt-in header.

    Parameters
    ----------
    request : HTTP request object

    Returns
    -------
    Returns whether the user wants to run fairshare tests during transfer
    """
    try:
        choice = request.META['HTTP_PRESQT_FAIRSHARE_EVALUATOR_OPT_IN']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'presqt-fairshare-evaluator-opt-in' missing in the request headers.",
            status.HTTP_400_BAD_REQUEST)

    if choice not in ['yes', 'no']:
        raise PresQTValidationError(
            "PresQT Error: 'presqt-fairshare-evaluator-opt-in' must be 'yes' or 'no'.",
            status.HTTP_400_BAD_REQUEST)

    if choice == 'yes':
        return True
    else:
        return False
