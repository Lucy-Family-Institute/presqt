from rest_framework import status

from presqt.exceptions import PresQTResponseException, PresQTInvalidTokenError
from presqt.osf.classes.main import OSF
from presqt.osf.helpers import get_osf_resource


def osf_fetch_resources(token):
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
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    resources = osf_instance.get_user_resources()
    return resources

def osf_fetch_resource(token, resource_id):
    """
    Fetch the OSF resource matching the resource_id given.

    Parameters
    ----------
    token : str
        User's OSF token

    resource_id : str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the OSF resource.
    """

    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    def create_object(resource_object):
        resource_object_obj = {
            'kind': resource_object.kind,
            'kind_name': resource_object.kind_name,
            'id': resource_object.id,
            'title': resource_object.title,
            'date_created': resource_object.date_created,
            'date_modified': resource_object.date_modified,
            'size': resource_object.size,
            'hashes': {
                'md5': resource_object.md5,
                'sha256': resource_object.sha256
            },
            'extra': {}
        }

        if resource_object.kind_name in ['folder', 'file']:
            resource_object_obj['extra'] = {
                'last_touched': resource_object.last_touched,
                'materialized_path': resource_object.materialized_path,
                'current_version': resource_object.current_version,
                'provider': resource_object.provider,
                'path': resource_object.path,
                'current_user_can_comment': resource_object.current_user_can_comment,
                'guid': resource_object.guid,
                'checkout': resource_object.checkout,
                'tags': resource_object.tags
            }
        elif resource_object.kind_name == 'project':
            resource_object_obj['extra'] = {
                'category': resource_object.category,
                'fork': resource_object.fork,
                'current_user_is_contributor': resource_object.current_user_is_contributor,
                'preprint': resource_object.preprint,
                'current_user_permissions': resource_object.current_user_permissions,
                'custom_citation': resource_object.custom_citation,
                'collection': resource_object.collection,
                'public': resource_object.public,
                'subjects': resource_object.subjects,
                'registration': resource_object.registration,
                'current_user_can_comment': resource_object.current_user_can_comment,
                'wiki_enabled': resource_object.wiki_enabled,
                'node_license': resource_object.node_license,
                'tags': resource_object.tags
            }
        return resource_object_obj

    # Get the resource
    resource = get_osf_resource(resource_id, osf_instance)

    return create_object(resource)
