import json

from rest_framework import status

from presqt.exceptions import PresQTValidationError


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
    with open('presqt/targets.json') as json_file:
        json_data = json.load(json_file)

    for data in json_data:
        if data['name'] == target_name:
            if data["supported_actions"][action] is False:
                raise PresQTValidationError(
                    "'{}' does not support the action '{}'.".format(target_name,action),
                    status.HTTP_400_BAD_REQUEST)
    else:
        raise PresQTValidationError(
            "'{}' is not a valid Target name.".format(target_name),
            status.HTTP_404_NOT_FOUND)
