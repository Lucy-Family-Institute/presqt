from rest_framework import status

from presqt.utilities import PresQTValidationError


def fairshare_request_validator(request):
    """
    Validate the request made by the user.

    Parameters
    ----------
    request: dict
        The request made by the user.

    Returns
    -------
        The resource_id and list of tests.
    """
    try:
        resource_id = request.data['resource_id']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'resource_id' missing in the request body.",
            status.HTTP_400_BAD_REQUEST)

    try:
        tests = request.data['tests']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'tests' missing in the request body.",
            status.HTTP_400_BAD_REQUEST)

    if type(tests) is not list:
        raise PresQTValidationError(
            "PresQT Error: 'tests' must be in list format.",
            status.HTTP_400_BAD_REQUEST)

    return resource_id, tests


def fairshare_test_validator(test_list, valid_tests):
    """
    Validate the list of tests passed by the user.

    Parameters
    ----------
    test_list: list
        List of tests the user wants to check
    valid_tests: dict
        The tests that PresQT has identified for this project.

    Returns
    -------
        The users list of tests.
    """
    list_of_valid_tests = [value['test_name'] for key, value in valid_tests.items()]

    # Check if empty list
    if len(test_list) == 0:
        raise PresQTValidationError(
            "PresQT Error: At least one test is required. Options are: {}".format(list_of_valid_tests),
            status.HTTP_400_BAD_REQUEST)

    # Ensure all tests in passed in list are valid
    for test in test_list:
        if test not in list_of_valid_tests:
            raise PresQTValidationError(
                "PresQT Error: '{}' not a valid test name. Options are: {}".format(test, list_of_valid_tests),
                status.HTTP_400_BAD_REQUEST)

    return test_list
