from rest_framework import status

from presqt.utilities import PresQTValidationError


def fairshake_request_validator(request, rubric_id):
    """
    Perform fairshake validation for required fields.

    Parameters
    ----------
    request : HTTP request object
    rubric_id: str
        The ID of the rubric the requesting user would like to use

    Returns
    -------
    Returns the rubric id, the digital object type, project url and project title
    """
    supported_rubrics = {
        "95": "tool",
        "94": "data",
        "93": "repo"
    }
    if rubric_id not in supported_rubrics.keys():
        raise PresQTValidationError(
            f"PresQT Error: '{rubric_id}' is not a valid rubric id. Options are: ['93', '94', '95']",
            status.HTTP_400_BAD_REQUEST)

    request_data = request.data

    try:
        project_url = request_data['project_url']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'project_url' missing in POST body.",
            status.HTTP_400_BAD_REQUEST)

    try:
        project_title = request_data['project_title']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'project_title' missing in POST body.",
            status.HTTP_400_BAD_REQUEST)

    return rubric_id, supported_rubrics[rubric_id], project_url, project_title
