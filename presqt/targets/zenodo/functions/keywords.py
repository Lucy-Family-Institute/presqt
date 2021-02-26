import json
import requests

from rest_framework import status

from presqt.targets.zenodo.utilities import zenodo_validation_check
from presqt.utilities import PresQTResponseException


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
    auth_parameter = zenodo_validation_check(token)

    from presqt.targets.zenodo.functions.fetch import zenodo_fetch_resource
    resource = zenodo_fetch_resource(token, resource_id)

    # Find the metadata file...
    metadata = None
    if resource['kind'] == 'container':
        file_url = "https://zenodo.org/api/deposit/depositions/{}/files".format(resource_id)
        project_files_response = requests.get(file_url, params=auth_parameter)

        if project_files_response.status_code == 200:
            for file in project_files_response.json():
                if file['filename'] == 'PRESQT_FTS_METADATA.json':
                    # Download the metadata
                    metadata_file = requests.get(
                        file['links']['download'], params=auth_parameter).content
                    metadata = json.loads(metadata_file)

    if 'keywords' in resource['extra'].keys():
        if metadata:
            try:
                keywords = list(set(resource['extra']['keywords'] + metadata['allKeywords']))
            except KeyError:
                keywords = list(set(resource['extra']['keywords']))
        else:
            keywords = list(set(resource['extra']['keywords']))

        return {
            'zenodo_keywords': keywords,
            'keywords': keywords}

    else:
        raise PresQTResponseException("The requested Zenodo resource does not have keywords.",
                                      status.HTTP_400_BAD_REQUEST)


def zenodo_upload_keywords(token, resource_id, keywords):
    """
    Upload the keywords to a given resource id.

    Parameters
    ----------
    token: str
        User's Zenodo token
    resource_id: str
        ID of the resource requested
    keywords: list
        List of new keywords to upload.

    Returns
    -------
    A dictionary object that represents the updated Zenodo resource keywords.
    Dictionary must be in the following format:
        {
            "updated_keywords": [
                'eggs',
                'EGG',
                'Breakfast'
            ]
        }
    """
    from presqt.targets.zenodo.functions.fetch import zenodo_fetch_resource

    resource = zenodo_fetch_resource(token, resource_id)

    project_id = resource_id
    if resource['kind_name'] == 'file':
        project_id = resource['container']
        # Get the top level project
        resource = zenodo_fetch_resource(token, project_id)

    headers = {"access_token": token}
    put_url = 'https://zenodo.org/api/deposit/depositions/{}'.format(project_id)

    try:
        upload_type = resource['extra']['upload_type']
    except KeyError:
        upload_type = "other"

    data = {'metadata': {
        "title": resource['title'],
        "upload_type": upload_type,
        "description": resource['extra']['description'],
        "creators": resource['extra']['creators'],
        "keywords": list(set(keywords))
    }}

    response = requests.put(put_url, params=headers, data=json.dumps(data),
                            headers={'Content-Type': 'application/json'})

    if response.status_code != 200:
        raise PresQTResponseException("Zenodo returned a {} error trying to update keywords.".format(
            response.status_code), status.HTTP_400_BAD_REQUEST)

    return {'updated_keywords': response.json()['metadata']['keywords'], "project_id": project_id}
