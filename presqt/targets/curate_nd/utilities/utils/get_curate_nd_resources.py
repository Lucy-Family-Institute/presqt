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
    try:
        resource = curate_nd_instance.resource(resource_id)
    except CurateNDForbiddenError as e:
        raise PresQTResponseException(
            "User does not have access to this resource with the token provided.", e.status_code)
    else:
        return resource
