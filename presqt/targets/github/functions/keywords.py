import base64
import json
import re

import requests

from rest_framework import status

from presqt.targets.github.utilities import validation_check
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
    header, username = validation_check(token)
    header['Accept'] = 'application/vnd.github.mercy-preview+json'
    from presqt.targets.github.functions.fetch import github_fetch_resource

    resource = github_fetch_resource(token, resource_id)
    if resource['kind_name'] in ['dir', 'file']:
        raise PresQTResponseException("GitHub directories and files do not have keywords.",
                                      status.HTTP_400_BAD_REQUEST)

    # See if a metadata file exists
    metadata = None
    project_data = requests.get(
        "https://api.github.com/repositories/{}".format(resource_id), headers=header)
    if project_data.status_code == 200:
        project_name = project_data.json()['name']
        metadata_url = "https://api.github.com/repos/{}/{}/contents/PRESQT_FTS_METADATA.json".format(
            username, project_name)
        metadata_file_data = requests.get(metadata_url, headers=header).json()
        try:
            sha = metadata_file_data['sha']
        except KeyError:
            sha = None
        if sha:
            base64_metadata = base64.b64decode(metadata_file_data['content'])
            metadata = json.loads(base64_metadata)

    if metadata:
        try:
            keywords = list(set(resource['extra']['topics'] + metadata['allKeywords']))
        except KeyError:
            keywords = list(set(resource['extra']['topics']))
    else:
        keywords = list(set(resource['extra']['topics']))
    return {
        'topics': keywords,
        'keywords': keywords}


def github_upload_keywords(token, resource_id, keywords):
    """
    Upload the keywords to a given resource id.

    Parameters
    ----------
    token: str
        User's GitHub token
    resource_id: str
        ID of the resource requested
    keywords: list
        List of new keywords to upload.

    Returns
    -------
    A dictionary object that represents the updated GitHub resource keywords.
    Dictionary must be in the following format:
        {
            "updated_keywords": [
                'eggs',
                'EGG',
                'Breakfast'
            ]
        }
    """
    from presqt.targets.github.functions.fetch import github_fetch_resource

    # This will raise an error if not a repo.
    resource = github_fetch_resource(token, resource_id)

    project_id = resource_id
    if resource['kind_name'] in ['file', 'dir']:
        project_id = resource['id'].partition(':')[0]
        resource = github_fetch_resource(token, project_id)

    headers = {"Authorization": "token {}".format(token),
               "Accept": "application/vnd.github.mercy-preview+json"}
    put_url = 'https://api.github.com/repositories/{}/topics'.format(project_id)

    # Start the new_keywords list with the resource's original topics
    new_keywords = resource['extra']['topics']
    for keyword in keywords:
        # Github can't have more than 20 topics
        if len(new_keywords) > 19:
            break
        # Github topics can't contain any special characters other than a hyphen, must be less
        # than 35 characters, and cannot be a single hyphen.
        if len(keyword) < 35 and keyword not in resource['extra']['topics']:
            stripped_keyword = re.sub('[^A-Za-z0-9-]+', '', keyword.lower())
            if stripped_keyword not in ['-', '']:
                new_keywords.append(stripped_keyword)
    data = {'names': list(set(new_keywords))}

    response = requests.put(put_url, headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise PresQTResponseException("GitHub returned a {} error trying to update keywords.".format(
            response.status_code), status.HTTP_400_BAD_REQUEST)

    return {'updated_keywords': response.json()['names'], 'project_id': project_id}
