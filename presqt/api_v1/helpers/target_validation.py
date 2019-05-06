import json

from rest_framework import status
from rest_framework.response import Response


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
    Response with details if the validation fails.
    """
    with open('presqt/targets.json') as json_file:
        json_data = json.load(json_file)

    for data in json_data:
        if data['name'] == target_name:
            if data["supported_actions"][action] is False:
                return Response(
                    data={'error': "'{}' does not support the action '{}'.".format(target_name,
                                                                                   action)},
                    status=status.HTTP_400_BAD_REQUEST)
            return True
    else:
        return Response(
            data={'error': "'{}' is not a valid Target name.".format(target_name)},
            status=status.HTTP_404_NOT_FOUND)
