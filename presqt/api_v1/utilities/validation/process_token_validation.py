from rest_framework import status

from presqt.exceptions import PresQTValidationError


def process_token_validation(token, process_info, token_name):
    """
    Ensure that the header token is the same one listed in the process_info file

    Parameters
    ----------
    token : str
        Token provided in the headers
    process_info : dict
        Process info from process_info.json
    token_name : str
        Name of the token we are looking to validate.
    """
    if token != process_info[token_name]:
        raise PresQTValidationError(
            "Header '{0}' does not match the '{0}' for this server process.".format(token_name),
            status.HTTP_401_UNAUTHORIZED)