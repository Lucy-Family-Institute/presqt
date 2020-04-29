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
                                      status.HTTP_404_NOT_FOUND)

    if 'tag_list' in resource['extra'].keys():
        return {
            'tag_list': resource['extra']['tag_list'],
            'keywords': resource['extra']['tag_list']
        }
    return {'tag_list': [], 'keywords': []}