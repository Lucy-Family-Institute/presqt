from rest_framework import status

from presqt.utilities import PresQTResponseException, PresQTInvalidTokenError
from presqt.targets.curate_nd.classes.main import CurateND
# from presqt.targets.curate_nd.helpers import get_osf_resource

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
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    resources = curate_instance.get_user_resources()
    return resources
