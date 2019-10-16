import base64
import fnmatch
import json
import os
import re
import requests

from natsort import natsorted
from rest_framework import status

from presqt.targets.github.utilities import validation_check, github_paginated_data
from presqt.utilities import PresQTResponseException


def github_upload_metadata(token, resource_id, resource_main_dir, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the repo.

    Parameters
    ----------
    token : str
        The user's GitHub token
    resource_id : str
        An id the upload is taking place on (not used for GitHub)
    resource_main_dir : str
        The path to the bag to be uploaded
    metadata_dict : dict
        The metadata to be written to the repo

    Returns
    -------
    """
    try:
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.',
                                      status.HTTP_401_UNAUTHORIZED)

    # Get the title of the repo to be written to.
    os_path = next(os.walk(resource_main_dir))
    # Note: GitHub doesn't allow spaces in repo_names
    repo_title = os_path[1][0].replace(' ', '_')
    github_data = github_paginated_data(token)

    titles = []
    for data in github_data:
        titles.append(data['name'])

    # Check for an exact match
    exact_match = repo_title in titles
    # Find only matches to the formatting that's expected in our title list
    duplicate_project_pattern = "{}-PresQT*-".format(repo_title)
    duplicate_project_list = fnmatch.filter(titles, duplicate_project_pattern)

    if exact_match and not duplicate_project_list:
        repo_title = repo_title

    elif duplicate_project_list:
        highest_duplicate_project = natsorted(duplicate_project_list)
        # findall takes a regular expression and a string, here we pass it the last number in
        # highest duplicate project, and it is returned as a list. int requires a string as an
        # argument, so the [0] is grabbing the only number in the list and converting it.
        highest_number = int(re.findall(r'\d+', highest_duplicate_project[-1])[0])
        repo_title = "{}-PresQT{}-".format(repo_title, highest_number)

    metadata_bytes = json.dumps(metadata_dict).encode('utf-8')
    base64_metadata = base64.b64encode(metadata_bytes).decode('utf-8')

    put_url = "https://api.github.com/repos/{}/{}/contents/PRESQT_FTS_METADATA.json".format(
        username, repo_title)

    data = {
        "message": "PresQT Upload",
        "committer": {
            "name": "PresQT",
            "email": "N/A"},
        "content": base64_metadata}

    requests.put(put_url, headers=header, data=json.dumps(data))
