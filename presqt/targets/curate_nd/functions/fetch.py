from rest_framework import status

from presqt.utilities import PresQTResponseException, PresQTInvalidTokenError
from presqt.targets.curate_nd.classes.main import CurateND
from presqt.targets.curate_nd.utilities import get_curate_nd_resource


def curate_nd_fetch_resources(token):
    """
    Fetch all CurateND resources (items, files) for the user connected to the given 'token'.

    Parameters
    ----------
    token : str
        User's CurateND token

    Returns
    -------
    List of dictionary objects that represent an CurateND resources.
    """
    try:
        curate_instance = CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException(
            "Token is invalid. Response returned a 401 status code.",
            status.HTTP_401_UNAUTHORIZED,
        )

    resources = curate_instance.get_user_resources()
    return resources


def curate_nd_fetch_resource(token, resource_id):
    """
    Fetch a single CurateND resource matching the resource id given.

    Parameters
    ----------
    token : str
        User's CurateND token

    resource_id : str
        ID of the resource requested.

    Returns
    -------
    A dictionary object that represents the CurateND resource.
    """
    try:
        curate_instance = CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException(
            "Token is invalid. Response returned a 401 status code.",
            status.HTTP_401_UNAUTHORIZED,
        )
    # Get the resource
    resource = get_curate_nd_resource(resource_id, curate_instance)
    resource_dict = {
        "kind": resource.kind,
        "kind_name": resource.kind_name,
        "id": resource.id,
        "title": resource.title,
        "date_created": resource.date_submitted,
        "date_modified": resource.modified,
        "hashes": {"md5": resource.md5, "sha256": resource.sha256},
        "extra": resource.extra}

    return resource_dict
