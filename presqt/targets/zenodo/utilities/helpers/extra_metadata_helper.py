import requests


def extra_metadata_helper(base_url, is_record, auth_parameter):
    """
    Build extra metadata dict to help with other integrations.

    Parameters
    ----------
    base_url: str
        Url to gather info on Zenodo project
    is_record: bool
        Is project a record or deposition (These have different payloads)
    auth_parameter: dict
        Zenodo Authorization param

    Returns
    -------
        Extra metadata dictionary
    """
    project_helper = requests.get(base_url, auth_parameter).json()

    if is_record:
        related_identifiers = [{"type":"doi", "id":project_helper['doi']}]
        license = project_helper['metadata']['license']['id']
        creators = [{
            "first_name": author['name'].partition(' ')[0],
            "last_name": author['name'].partition(' ')[2],
            "ORCID": None
        } for author in project_helper['metadata']['creators']]
    else:
        related_identifiers = [{"type": "doi", "id": project_helper['metadata']['prereserve_doi']['doi']}]
        license = project_helper['metadata']['license']
        creators = [{
            "first_name": author['name'].partition(", ")[2],
            "last_name": author['name'].partition(", ")[0],
            "ORCID": None
        } for author in project_helper['metadata']['creators']]

    extra_metadata = {
        "title": project_helper['metadata']['title'],
        "creators": creators,
        "publication_date": project_helper['metadata']['publication_date'],
        "description": project_helper['metadata']['description'],
        "keywords": project_helper['metadata']['keywords'],
        "license": license,
        "related_identifiers": related_identifiers,
        "references": None,
        "notes": None
    }

    return extra_metadata
