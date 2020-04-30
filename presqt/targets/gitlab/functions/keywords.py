import json
import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def gitlab_fetch_keywords(token, resource_id):
    """
    Fetch the keywords of a given resource id.

    Parameters
    ----------
    token: str
        User's GitLab token
    resource_id: str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the GitLab resource keywords.
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
    from presqt.targets.gitlab.functions.fetch import gitlab_fetch_resource

    resource = gitlab_fetch_resource(token, resource_id)

    if resource['kind_name'] in ['dir', 'file']:
        raise PresQTResponseException("GitLab directories and files do not have keywords.",
                                      status.HTTP_400_BAD_REQUEST)

    if 'tag_list' in resource['extra'].keys():
        return {
            'tag_list': resource['extra']['tag_list'],
            'keywords': resource['extra']['tag_list']
        }


def gitlab_upload_keywords(token, resource_id, keywords):
    """
    Upload the keywords to a given resource id.

    Parameters
    ----------
    token: str
        User's GitLab token
    resource_id: str
        ID of the resource requested
    keywords: list
        List of new keywords to upload.

    Returns
    -------
    A dictionary object that represents the updated GitLab resource keywords.
    Dictionary must be in the following format:
        {
            "updated_keywords": [
                'eggs',
                'EGG',
                'Breakfast'
            ]
        }
    """
    from presqt.targets.gitlab.functions.fetch import gitlab_fetch_resource

    # This will raise an error if not a project.
    gitlab_fetch_resource(token, resource_id)

    headers = {"Private-Token": "{}".format(token)}
    put_url = 'https://gitlab.com/api/v4/projects/{}'.format(resource_id)

    new_keywords = [keyword.lower() for keyword in keywords]

    new_keywords_string = ','.join(list(set(new_keywords)))

    response = requests.put("{}?tag_list={}".format(put_url, new_keywords_string), headers=headers)

    if response.status_code != 200:
        raise PresQTResponseException("GitLab returned a {} error trying to update keywords.".format(
            response.status_code), status.HTTP_400_BAD_REQUEST)

    return {'updated_keywords': response.json()['tag_list']}
