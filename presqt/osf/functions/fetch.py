from rest_framework import status

from presqt.exceptions import PresQTResponseException, PresQTInvalidTokenError
from presqt.osf.classes.main import OSF
from presqt.osf.exceptions import OSFNotFoundError


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

    osf_instance = OSF(token)
    try:
        resources = osf_instance.get_user_resources()
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
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

    osf_instance = OSF(token)

    def create_object(resource_obj):
        return {
            'kind': resource_obj.kind,
            'kind_name': resource_obj.kind_name,
            'id': resource_obj.id,
            'title': resource_obj.title,
            'date_created': resource_obj.date_created,
            'date_modified': resource_obj.date_modified,
            'size': resource_obj.size
        }

    # Since we don't know the file type, try and get the resource as a storage provider first.
    resource_id_split = resource_id.split(':')
    try:
        resource = osf_instance.project(resource_id_split[0]).storage(resource_id_split[1])
    except OSFNotFoundError:
        pass
    except IndexError:
        pass
    else:
        return create_object(resource)

    # If it's not a storage provider then check if it's a file or folder.
    try:
        resource = osf_instance.resource(resource_id)
    except OSFNotFoundError:
        pass
    else:
        return create_object(resource)

    # If it's not a folder/file then it's a project.
    try:
        resource = osf_instance.project(resource_id)
    except OSFNotFoundError as e:
        raise PresQTResponseException(
            "Resource with id '{}' not found for this user.".format(resource_id), e.status_code)
    else:
        return create_object(resource)

