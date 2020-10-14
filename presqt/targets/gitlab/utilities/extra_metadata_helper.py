import requests


def extra_metadata_helper(json_content, headers):
    """
    Build extra metadata dict to help with other integrations.

    Parameters
    ----------
    json_content: dict
        Information about the GitLab repo
    headers: dict
        GitLab Authorization header

    Returns
    -------
        Extra metadata dictionary
    """
    # Get user name information
    split_name = json_content['owner']['name'].partition(' ')
    first_name = split_name[0]
    last_name = split_name[2]

    # Get the license if it exists
    license = None
    license_data = requests.get("{}/managed_licenses".format(json_content['_links']['self']),
                                headers=headers)
    if license_data.status_code == 200:
        if len(license_data.json()) > 0:
            license = license_data.json()[0]['name']

    extra_metadata = {
        "title": json_content['name'],
        "creators": [
            {
                "first_name": first_name,
                "last_name": last_name,
                "ORCID": None
            }
        ],
        "publication_date": json_content['created_at'],
        "description": json_content['description'],
        "keywords": json_content['tag_list'],
        "license": license,
        "related_identifiers": [],
        "references": None,
        "notes": None
    }

    return extra_metadata
