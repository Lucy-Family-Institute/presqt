from rest_framework import status

from presqt.utilities import read_file
from presqt.utilities import PresQTValidationError


def get_process_info_data(action, ticket_number):
    """
    Get the JSON from process_info.json in the requested ticket number directory.

    Parameters
    ----------
    action : str
        The action directory we should look in for the ticket_number directory
    ticket_number : str
        Requested ticket_number directory the JSON should live in

    Returns
    -------
    JSON dictionary representing the process_info.json data.
    """
    try:
        return read_file('mediafiles/{}/{}/process_info.json'.format(action, ticket_number), True)
    except FileNotFoundError:
        raise PresQTValidationError("PresQT Error: Invalid ticket number, '{}'.".format(ticket_number),
                                    status.HTTP_404_NOT_FOUND)