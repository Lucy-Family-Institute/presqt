import requests


def extra_metadata_helper(project_url, headers):
    """
    Build extra metadata dict to help with other integrations.

    Parameters
    ----------
    project_url: str
        The url to the project info
    headers: dict
        Figshare Authorization header

    Returns
    -------
        Extra metadata dictionary
    """
    project_info = requests.get(project_url, headers=headers).json()

    creators = [{
        "first_name": author['name'].partition(' ')[0],
        "last_name": author['name'].partition(' ')[2],
        'ORCID': None
    } for author in project_info['collaborators']]

    publication_date = project_info['created_date']
    if 'published_date' in project_info.keys():
        publication_date = project_info['published_date']

    extra_metadata = {
        "title": project_info['title'],
        "creators": creators,
        "publication_date": publication_date,
        "description": project_info['description'],
        "keywords": [],
        "license": None,
        "related_identifiers": [],
        "references": None,
        "notes": None
    }
    print(extra_metadata)
    return extra_metadata