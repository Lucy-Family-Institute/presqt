from rest_framework import status

from presqt.utilities import PresQTResponseException, PresQTInvalidTokenError
from presqt.targets.curate_nd.classes.main import CurateND
from presqt.targets.curate_nd.helpers import get_curate_nd_resource


def curate_nd_fetch_resources(token):
    """
    Fetch all OSF resources (projects/nodes, folders, files) for the user connected
    to the given 'token'.

    Parameters
    ----------
    token : str
        User's OSF token

    Returns
    -------
    List of dictionary objects that represent an OSF resources.
    """
    try:
        curate_instance = CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 403 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    resources = curate_instance.get_user_items()
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
        raise PresQTResponseException("Token is invalid. Response returned a 403 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    def create_object(resource_object):
        resource_object_obj = {
            'kind': resource_object.kind,
            'kind_name': resource_object.kind_name,
            'id': resource_object.id,
            'title': resource_object.title,
            'date_created': resource_object.date_submitted,
            'date_modified': resource_object.modified,
            'size': resource_object.size,
            'hashes': {
                'md5': resource_object.md5,
                'sha256': resource_object.sha256},
            'extra': {}}

        if resource_object.kind_name == 'item':
            resource_object_obj['extra'] = {
                'creator': resource_object.creator,
                'access': resource_object.access,
                'depositor': resource_object.depositor,
                'owner': resource_object.owner,
                'has_model': resource_object.has_model,
                'contained_files': resource_object.contained_files}

        return resource_object_obj

    # Get the resource
    resource = get_curate_nd_resource(resource_id, curate_instance)

    return create_object(resource)
