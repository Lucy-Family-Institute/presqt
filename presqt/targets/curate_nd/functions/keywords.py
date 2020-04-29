from rest_framework import status

from presqt.targets.curate_nd.classes.main import CurateND
from presqt.targets.curate_nd.utilities import get_curate_nd_resource
from presqt.utilities import PresQTResponseException, PresQTInvalidTokenError


def curate_nd_fetch_keywords(token, resource_id):
    """
    Fetch the keywords of a given resource id.

    Parameters
    ----------
    token: str
        User's CurateND token
    resource_id: str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the CurateND resource keywords.
    Dictionary must be in the following format:
        {
            "subject": [
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
        curate_instance = CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    resource = get_curate_nd_resource(resource_id, curate_instance)

    if 'subject' in resource.extra.keys():
        return {'subject': resource.extra['subject'], 'keywords': resource.extra['subject']}

    else:
        raise PresQTResponseException(
            "The given resouce id does not support keywords.", status.HTTP_400_BAD_REQUEST)
