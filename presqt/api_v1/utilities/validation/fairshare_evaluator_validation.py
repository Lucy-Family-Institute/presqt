from rest_framework import status

from presqt.utilities import PresQTValidationError


def fairshare_evaluator_validation(request):
    """
    Get the appropriate data from the request body for FAIRShare Evaluator.
    """

    try:
        resource_id = request.data['resource_id']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'resource_id' missing in the request body.",
            status.HTTP_400_BAD_REQUEST)

    try:
        executor = request.data['executor']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'executor' missing in the request body.",
            status.HTTP_400_BAD_REQUEST)

    try:
        title = request.data['title']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'title' missing in the request body.",
            status.HTTP_400_BAD_REQUEST)

    return resource_id, executor, title