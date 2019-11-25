from presqt.targets.osf.utilities import OSFNotFoundError
from presqt.utilities import PresQTResponseException


def get_osf_resource(resource_id, osf_instance):
    """
    Get an OSF resource based on a given id.

    Parameters
    ----------
    resource_id : str
        Resource ID to retrieve.

    osf_instance : OSF class object
        Instance of the OSF class we want to use to get the resource from.

    Returns
    -------
    The class object for the resource requested.
    """
    # Since we don't know the file type, try and get the resource as a storage provider first.
    resource_id_split = resource_id.split(':')
    try:
        resource = osf_instance.project(resource_id_split[0]).storage(resource_id_split[1])
    except (OSFNotFoundError, IndexError):
        pass
    else:
        return resource

    # If it's not a storage provider then check if it's a file or folder.
    try:
        resource = osf_instance.resource(resource_id)
    except OSFNotFoundError:
        pass
    else:
        return resource

    # If it's not a folder/file then it's a project or it doesn't exist.
    try:
        resource = osf_instance.project(resource_id)
    except OSFNotFoundError as e:
        raise PresQTResponseException(
            "Resource with id '{}' not found for this user.".format(resource_id), e.status_code)
    else:
        return resource
