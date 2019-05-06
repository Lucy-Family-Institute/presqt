import json

from rest_framework import status

from presqt.exceptions import ValidationException, AuthorizationException


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
                raise ValidationException(
                    "'{}' does not support the action '{}'.".format(target_name,action),
                    status.HTTP_400_BAD_REQUEST)
            return True
    else:
        raise ValidationException(
            "'{}' is not a valid Target name.".format(target_name),
            status.HTTP_404_NOT_FOUND)


def token_validation(request):
    """
    Perform token validation.

    Parameters
    ----------
    request : HTTP request object

    Returns
    -------
    Returns the token if the validation is successful.
    Raises a custom AuthorizationException error if the validation fails.
    """
    # Validate that the proper token exists in the request.
    try:
        return request.META['HTTP_PRESQT_SOURCE_TOKEN']
    except KeyError:
        raise AuthorizationException(
            "'presqt-source-token' missing in the request headers.",
            status.HTTP_400_BAD_REQUEST)