from rest_framework import status

from presqt.utilities import PresQTValidationError


def get_process_info_action(process_info_data, action):
    """
    Get an action's data in the process_info dict

    Parameters
    ----------
    process_info_data: dict
        Dict gathered from the process_info.json file
    action: str
        Action data we want from process_info_data

    Returns
    -------
    Dict of the action data
    """

    try:
        return process_info_data[action]
    except KeyError:
        raise PresQTValidationError("PresQT Error: A {} does not exist for this user on the server.".format(action),
                                    status.HTTP_404_NOT_FOUND)
