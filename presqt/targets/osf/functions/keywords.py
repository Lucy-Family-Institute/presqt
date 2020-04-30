import json
import requests

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

    if resource.kind_name == 'storage':
        raise PresQTResponseException("OSF Storages do not have keywords.",
                                      status.HTTP_400_BAD_REQUEST)

    return {'tags': resource.tags, 'keywords': resource.tags}


def osf_upload_keywords(token, resource_id, keywords):
    """
    Upload the keywords to a given resource id.

    Parameters
    ----------
    token: str
        User's OSF token
    resource_id: str
        ID of the resource requested
    keywords: list
        List of new keywords to upload

    Returns
    -------
    A dictionary object that represents the updated OSF resource keywords.
    Dictionary must be in the following format:
        {
            "updated_keywords": [
                'eggs',
                'EGG',
                'Breakfast'
            ]
        }
    """
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    headers = {'Authorization': 'Bearer {}'.format(token), 'Content-Type': 'application/json'}

    resource = get_osf_resource(resource_id, osf_instance)

    if resource.kind_name == 'project':
        patch_url = 'https://api.osf.io/v2/nodes/{}/'.format(resource_id)
        data = {"data": {"type": "nodes", "id": resource_id, "attributes": {"tags": keywords}}}

    elif resource.kind_name == 'file':
        patch_url = 'https://api.osf.io/v2/files/{}/'.format(resource_id)
        data = {"data": {"type": "files", "id": resource_id, "attributes": {"tags": keywords}}}

    elif resource.kind_name == 'folder':
        raise PresQTResponseException("Can not update OSF folder keywords.",
                                      status.HTTP_400_BAD_REQUEST)

    response = requests.patch(patch_url, headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise PresQTResponseException("OSF returned a {} error trying to update keywords.".format(
            response.status_code), status.HTTP_400_BAD_REQUEST)

    return {"updated_keywords": response.json()['data']['attributes']['tags']}
