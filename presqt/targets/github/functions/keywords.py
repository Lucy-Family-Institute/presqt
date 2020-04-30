import json
import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def github_fetch_keywords(token, resource_id):
    """
    Fetch the keywords of a given resource id.

    Parameters
    ----------
    token: str
        User's GitHub token
    resource_id: str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the GitHub resource keywords.
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
    from presqt.targets.github.functions.fetch import github_fetch_resource

    resource = github_fetch_resource(token, resource_id)

    if resource['kind_name'] in ['dir', 'file']:
        raise PresQTResponseException("GitHub directories and files do not have keywords.",
                                      status.HTTP_400_BAD_REQUEST)

    if 'topics' in resource['extra'].keys():
        return {
            'topics': resource['extra']['topics'],
            'keywords': resource['extra']['topics']
        }


def github_upload_keywords(token, resource_id, keywords):
    """
    Upload the keywords to a given resource id.

    Parameters
    ----------
    token: str
        User's GitHub token
    resource_id: str
        ID of the resource requested
    keywords: list
        List of new keywords to upload.

    Returns
    -------
    A dictionary object that represents the updated GitHub resource keywords.
    Dictionary must be in the following format:
        {
            "updated_keywords": [
                'eggs',
                'EGG',
                'Breakfast'
            ]
        }
    """
    from presqt.targets.github.functions.fetch import github_fetch_resource

    # This will raise an error if not a repo.
    resource = github_fetch_resource(token, resource_id)

    headers = {"Authorization": "token {}".format(token),
               "Accept": "application/vnd.github.mercy-preview+json"}
    put_url = 'https://api.github.com/repos/{}/topics'.format(resource['extra']['full_name'])

    new_keywords = []
    for keyword in keywords:
        if len(keyword) < 35:
            new_keywords.append(keyword.lower().replace(' ', '-'))

    data = {'names': list(set(new_keywords))}

    response = requests.put(put_url, headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise PresQTResponseException("GitHub returned a {} error trying to update keywords.".format(
            response.status_code), status.HTTP_400_BAD_REQUEST)

    return {'updated_keywords': response.json()['names']}
