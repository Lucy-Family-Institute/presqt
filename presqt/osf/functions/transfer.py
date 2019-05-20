from rest_framework import status

from presqt.exceptions import PresQTResponseException, PresQTInvalidTokenError
from presqt.osf.classes.main import OSF
from presqt.osf.helpers import get_osf_resource


def osf_download_resource(token, resource_id):
    """
    Fetch the requested resource from OSF along with it's class representation.

    Parameters
    ----------
    token : str
        User's OSF token.

    resource_id : str
        ID of the resource requested.

    Returns
    -------
    A dictionary object that contains the file to download, the resource class, and any other
    relevant information.
    """

    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    # Get the resource
    resource = get_osf_resource(resource_id, osf_instance)

    # Make a download request to OSF.
    binary_file = resource.download()

    # Only continue if the resource ends up being a file.
    if resource.kind_name == 'file':
        return {
            'file': binary_file,
            'resource': resource,
        }
    else:
        raise PresQTResponseException(
                "Resource with id, '{}', is not a file.".format(resource_id),
                status.HTTP_400_BAD_REQUEST)

