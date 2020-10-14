import requests


def extra_metadata_helper(json_content, repo_name, header):
    """
    Build extra metadata dict to help with other integrations.

    Parameters
    ----------
    json_content: dict
        Information about the GitHub repo
    repo_name: str
        The name of this GitHub repository
    header: dict
        GitHub Authorization header

    Returns
    -------
        Extra metadata dictionary
    """
    # Build up extra metadata
    name_helper = requests.get(json_content['owner']['url'], headers=header)
    first_name = None
    last_name = None

    if name_helper.status_code == 200:
        try:
            name = name_helper.json()['name'].partition(' ')
            first_name = name[0]
            last_name = name[2]
        except AttributeError:
            pass

    try:
        license = json_content['license']['name']
    except TypeError:
        license = None

    extra_metadata = {
        "title": repo_name,
        "creators": [
            {
                "first_name": first_name,
                "last_name": last_name,
                "ORCID": None
            }
        ],
        "publication_date": json_content['created_at'],
        "description": json_content['description'],
        "keywords": json_content['topics'],
        "license": license,
        "related_identifiers": [],
        "references": None,
        "notes": None
    }

    return extra_metadata
