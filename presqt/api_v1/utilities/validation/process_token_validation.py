from rest_framework import status

from presqt.exceptions import PresQTValidationError


def process_token_validation(token, data_token):
    """
    Ensure that the header token is the same one listed in the process_info file

    Parameters
    ----------
    token : str
        Token provided in the headers
    data_token : str
        Token found in the process_info.json
    """
    if token != data_token:
        raise PresQTValidationError("Header 'presqt-source-token' does not match the "
                                    "'presqt-source-token' for this server process.",
                                    status.HTTP_401_UNAUTHORIZED)