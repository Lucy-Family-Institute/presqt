import base64
import json
import requests

from rest_framework import status

from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.utilities import PresQTResponseException


def figshare_fetch_keywords(token, resource_id):
    """
    Fetch the keywords of a given resource id.

    Parameters
    ----------
    token: str
        User's FigShare token
    resource_id: str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the FigShare resource keywords.
    Dictionary must be in the following format:
        {
            "topics": [
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
        headers, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    split_id = resource_id.split(":")
    if len(split_id) == 1 or len(split_id) == 3:
        raise PresQTResponseException("FigShare projects/files do no have keywords.",
                                      status.HTTP_400_BAD_REQUEST)

    from presqt.targets.figshare.functions.fetch import figshare_fetch_resource
    resource = figshare_fetch_resource(token, resource_id)

    # Since keywords only exist on the article level, we won't look into the metadata file whilst
    # retrieving keywords for FigShare.
    keywords = list(set(resource['extra']['tags']))

    return {
        "tags": keywords,
        "keywords": keywords
    }
