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
                                      status.HTTP_404_NOT_FOUND)

    if 'topics' in resource['extra'].keys():
        return {
            'topics': resource['extra']['topics'],
            'keywords': resource['extra']['topics']
        }
    return {'topics': [], 'keywords': []}
