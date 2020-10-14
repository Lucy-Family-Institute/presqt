import requests


def extra_metadata_helper(resource_id, headers):
    """
    Build extra metadata dict to help with other integrations.

    Parameters
    ----------
    resource_id: str
        The OSF resource ID
    headers: dict
        OSF Authorization header

    Returns
    -------
        Extra metadata dictionary
    """
    # Get project information
    base_url = "https://api.osf.io/v2/nodes/{}/".format(resource_id)
    project_info = requests.get(base_url, headers=headers).json()

    # Build creators list
    citation_data = requests.get("{}citation/".format(base_url), headers=headers).json()
    creators = [{
        "first_name": author['given'],
        "last_name": author['family'],
        "ORCID": None} for author in citation_data['data']['attributes']['author']]

    # Get license if it exists
    license = None
    if 'license' in project_info['data']['relationships'].keys():
        license_data = requests.get(project_info['data']['relationships']['license']['links']['related']['href'],
                                    headers=headers).json()
        if license_data['data']['attributes']:
            license = license_data['data']['attributes']['name']
    
    # See if there's an identifier for this project
    identifier_data = requests.get("{}identifiers/".format(base_url), headers=headers).json()
    identifiers = [{
        "type": identifier['attributes']['category'],
        "identifier": identifier['attributes']['value']} for identifier in identifier_data['data']]

    extra_metadata = {
        "title": project_info['data']['attributes']['title'],
        "creators": creators,
        "publication_date": project_info['data']['attributes']['date_created'],
        "description": project_info['data']['attributes']['description'],
        "keywords": project_info['data']['attributes']['tags'],
        "license": license,
        "related_identifiers": identifiers,
        "references": None,
        "notes": None
    }

    print(extra_metadata)
    return extra_metadata
