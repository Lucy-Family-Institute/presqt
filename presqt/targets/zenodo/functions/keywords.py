

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
    return {'zenodo_keywords': [], 'keywords': []}
