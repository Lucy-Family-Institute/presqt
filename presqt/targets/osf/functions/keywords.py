from rest_framework import status

from presqt.targets.osf.classes.main import OSF
from presqt.targets.osf.utilities import get_osf_resource
from presqt.utilities import PresQTResponseException, PresQTInvalidTokenError


def osf_fetch_keywords(token, resource_id):
    """
    Fetch the keywords of a given resource id.

    Parameters
    ----------
    token: str
        User's OSF token
    resource_id: str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the OSF resource keywords.
    Dictionary must be in the following format:
        {
            "tags": [
                "eggs",
                "ham",
                "bacon"
            ],
            "keywords": [
                "eggs",
                "ham",
                "bacon"
            ]
        }
    """
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    resource = get_osf_resource(resource_id, osf_instance)

    return {'tags': resource.tags, 'keywords': resource.tags}


def osf_upload_keywords(token, resource_id, action):
    """
    """
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    new_list_of_keywords = []

    return {"new_tags": new_list_of_keywords}
