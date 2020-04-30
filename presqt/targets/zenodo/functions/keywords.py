import json
import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def zenodo_fetch_keywords(token, resource_id):
    """
    Fetch the keywords of a given resource id.

    Parameters
    ----------
    token: str
        User's Zenodo token
    resource_id: str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the Zenodo resource keywords.
    Dictionary must be in the following format:
        {
            "zenodo_keywords": [
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
    from presqt.targets.zenodo.functions.fetch import zenodo_fetch_resource

    resource = zenodo_fetch_resource(token, resource_id)

    if 'keywords' in resource['extra'].keys():
        return {
            'zenodo_keywords': resource['extra']['keywords'],
            'keywords': resource['extra']['keywords']
        }

    else:
        # Files don't have keywords
        raise PresQTResponseException("Zenodo files do not have keywords.",
                                      status.HTTP_400_BAD_REQUEST)


def zenodo_upload_keywords(token, resource_id, keywords):
    """
    Upload the keywords to a given resource id.

    Parameters
    ----------
    token: str
        User's Zenodo token
    resource_id: str
        ID of the resource requested
    keywords: list
        List of new keywords to upload.

    Returns
    -------
    A dictionary object that represents the updated Zenodo resource keywords.
    Dictionary must be in the following format:
        {
            "updated_keywords": [
                'eggs',
                'EGG',
                'Breakfast'
            ]
        }
    """
    from presqt.targets.zenodo.functions.fetch import zenodo_fetch_resource

    resource = zenodo_fetch_resource(token, resource_id)

    headers = {"access_token": token}
    put_url = 'https://zenodo.org/api/deposit/depositions/{}'.format(resource_id)

    data = {'metadata': {
        "title": resource['title'],
        "upload_type": resource['extra']['upload_type'],
        "description": resource['extra']['description'],
        "creators": resource['extra']['creators'],
        "keywords": list(set(keywords))
    }}

    response = requests.put(put_url, params=headers, data=json.dumps(data),
                            headers={'Content-Type': 'application/json'})

    if response.status_code != 200:
        raise PresQTResponseException("Zenodo returned a {} error trying to update keywords.".format(
            response.status_code), status.HTTP_400_BAD_REQUEST)

    return {'updated_keywords': response.json()['metadata']['keywords']}
