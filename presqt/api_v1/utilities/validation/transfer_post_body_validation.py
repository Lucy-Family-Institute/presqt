from rest_framework import status

from presqt.utilities import PresQTValidationError


def transfer_post_body_validation(request):
    """
    Extract target_name and resource_id from the request body.

    Parameters
    ----------
    request: HTTP Request Object

    Returns
    -------
    source_target:
        Name of the target that owns the resource to be transferred.
    source_resource_id:
        ID of the resource to transfer.
    """
    request_data = request.data

    try:
        source_target = request_data['source_target_name']
    except KeyError:
        raise PresQTValidationError(
            "source_target_name was not found in the request body.", status.HTTP_400_BAD_REQUEST)

    try:
        source_resource_id = request_data['source_resource_id']
    except KeyError:
        raise PresQTValidationError(
            "source_resource_id was not found in the request body.", status.HTTP_400_BAD_REQUEST)

    if source_resource_id is None or source_resource_id == "":
        raise PresQTValidationError(
            "source_resource_id can't be None or blank.", status.HTTP_400_BAD_REQUEST)

    return source_target, source_resource_id