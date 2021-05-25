from rest_framework import status

from presqt.utilities import PresQTValidationError


def get_user_email_opt(request):
    """
    Perform email validation for the presqt-email-opt-in header.

    Parameters
    ----------
    request : HTTP request object

    Returns
    -------
    Returns the email address if the validation is successful.
    Raises a custom AuthorizationException error if the validation fails.
    """
    try:
        return request.META['HTTP_PRESQT_EMAIL_OPT_IN']
    except KeyError:
        # If it's not in the headers, just don't send an email
        return False
