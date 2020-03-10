from rest_framework import status

from presqt.utilities import PresQTValidationError, read_file


def target_validation(target_name, action):
    """
    Given a Target name and an action, determine if the target_name is a valid
    target in target.json and if the target supports the action.

    Parameters
    ----------
    target_name : str
        Name of the Target.
    action : str
        Type of action the API is looking to perform on the Target

    Returns
    -------
    True if the validation passes.
    Raises a custom ValidationException error if validation fails.
    """
    json_data = read_file('presqt/targets.json', True)
    for data in json_data:
        if data['name'] == target_name:
            if data["supported_actions"][action] is False:
                raise PresQTValidationError(
                    "PresQT Error: '{}' does not support the action '{}'.".format(target_name, action),
                    status.HTTP_400_BAD_REQUEST)
            return True, data['infinite_depth']
    else:
        raise PresQTValidationError(
            "PresQT Error: '{}' is not a valid Target name.".format(target_name), status.HTTP_404_NOT_FOUND)


def transfer_target_validation(source_target, destination_target):
    """
    Validation check for pending transfer partners.

    Parameters
    ----------
    source_target : str
        The source target (where the transfer is coming from)
    destination_target : str
        The destination target (where the transfer will end up)

    Raises
    ------
    PresQT Validation Error if targets don't allow transfer to or from other target.

    Returns
    -------
    True if the targets allow transfer with each other.
    """
    json_data = read_file('presqt/targets.json', True)

    for data in json_data:
        if data['name'] == source_target:
            if destination_target not in data['supported_transfer_partners']['transfer_out']:
                raise PresQTValidationError(
                    "PresQT Error: '{}' does not allow transfer to '{}'.".format(
                        source_target, destination_target),
                    status.HTTP_400_BAD_REQUEST)

        elif data['name'] == destination_target:
            if source_target not in data['supported_transfer_partners']['transfer_in']:
                raise PresQTValidationError(
                    "PresQT Error: '{}' does not allow transfer from '{}'.".format(
                        destination_target, source_target),
                    status.HTTP_400_BAD_REQUEST)

    return True
