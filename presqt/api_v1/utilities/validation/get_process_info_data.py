import json

from rest_framework import status
from presqt.utilities import read_file
from presqt.utilities import PresQTValidationError


def get_process_info_data(ticket_number):
    """
    Get the JSON from process_info.json in the requested ticket number directory.

    Parameters
    ----------
    ticket_number : str
        Requested ticket_number directory the JSON should live in

    Returns
    -------
    JSON dictionary representing the process_info.json data.
    """
    while True:
        try:
            return read_file('mediafiles/jobs/{}/process_info.json'.format(ticket_number), True)
        except json.decoder.JSONDecodeError:
            pass
        except FileNotFoundError:
            raise PresQTValidationError("PresQT Error: Invalid ticket number, '{}'.".format(ticket_number),
                                        status.HTTP_404_NOT_FOUND)