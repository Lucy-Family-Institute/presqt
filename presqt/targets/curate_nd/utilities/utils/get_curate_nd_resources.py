from presqt.utilities import PresQTResponseException
from presqt.targets.curate_nd.utilities import CurateNDForbiddenError


def get_curate_nd_resource(resource_id, curate_nd_instance):
    """
    Get a CurateND resource based on a given id.

    Parameters
    ----------
    resource_id : str
        Resource ID to retrieve

    curate_nd_instance : CurateND class object
        Instance of the CurateND class we want to use to get the resource from.

    Returns
    -------
    The class object for the resource requested.
    """
    # Item
    try:
        resource = curate_nd_instance.item(resource_id)
    except CurateNDForbiddenError as e:
        raise PresQTResponseException(
            "Resource with id '{}' not found for this user.".format(resource_id), e.status_code)
    else:
        return resource

    # File
    try:
        resource = curate_nd_instance.file(resource_id)
    except CurateNDForbiddenError as e:
        raise PresQTResponseException(
            "Resource with id '{}' not available for this user.".format(resource_id), e.status_code)
    else:
        return resource
