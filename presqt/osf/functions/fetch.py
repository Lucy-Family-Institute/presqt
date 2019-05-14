from presqt.exceptions import PresQTResponseException
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

    osf_instance = OSF(token)



    try:
        resource_id_split = resource_id.split(':')
    except IndexError:
        pass
    else:
        try:
            storage = osf_instance.project(resource_id_split[0]).storage(resource_id_split[1])
        except OSFNotFoundError:
            pass
        else:
            return {
                'id': storage.id,
                'title': storage.title
            }


    # Since we don't know the file type, try and get the resource as a file or folder first.
    try:
        resource = osf_instance.resource(resource_id)
    except OSFNotFoundError:
        pass
    else:
        return {
            'id': resource.id,
            'title': resource.title
        }

    # If it's not a folder/file then it's a project.
    try:
        resource = osf_instance.project(resource_id)
    except OSFNotFoundError as e:
        raise PresQTResponseException(
            "Resource with id '{}' not found for this user.".format(resource_id), e.status_code)
    else:
        return {
            'id': resource.id,
            'title': resource.title
        }
