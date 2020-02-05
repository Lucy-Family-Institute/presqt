import base64
import json
import os
import requests

from rest_framework import status

from presqt.targets.github.utilities import validation_check, create_repository
from presqt.utilities import PresQTResponseException


def github_upload_resource(token, resource_id, resource_main_dir, hash_algorithm, file_duplicate_action):
    """
    Upload the files found in the resource_main_dir to the target.

    Parameters
    ----------
    token : str
        User's token.
    resource_id : str
        ID of the resource requested.
    resource_main_dir : str
        Path to the main directory for the resources to be uploaded.
    hash_algorithm : str
        Hash algorithm we are using to check for fixity.
    file_duplicate_action : str
        The action to take when a duplicate file is found

    Returns
    -------
    Dictionary with the following keys: values
        'resources_ignored' : Array of string file paths of files that were ignored when
        uploading the resource. Path should have the same base as resource_main_dir.
                                Example:
                                    ['path/to/ignored/file.pg', 'another/ignored/file.jpg']

        'resources_updated' : Array of string file paths of files that were updated when
         uploading the resource. Path should have the same base as resource_main_dir.
                                 Example:
                                    ['path/to/updated/file.jpg']
        'action_metadata': Dictionary containing action metadata. Must be in the following format:
                            {
                                'destinationUsername': 'some_username'
                            }
        'file_metadata_list': List of dictionaries for each file that contains metadata
                              and hash info. Must be in the following format:
                                {
                                    "actionRootPath": '/path/on/disk',
                                    "destinationPath": '/path/on/target/destination',
                                    "title": 'file_title',
                                    "destinationHash": {'hash_algorithm': 'the_hash'}}
                                }
        'project_id': ID of the parent project for this upload. Needed for metadata upload.
    """
    # Uploading to an existing Github repository is not allowed
    if resource_id:
        raise PresQTResponseException("Can't upload to an existing Github repository.",
                                      status.HTTP_400_BAD_REQUEST)

    try:
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    os_path = next(os.walk(resource_main_dir))

    # Create a new repository with the name being the top level directory's name.
    # Note: GitHub doesn't allow spaces in repo_names
    repo_title = os_path[1][0].replace(' ', '_')
    title = create_repository(repo_title, token)

    resources_ignored = []
    action_metadata = {"destinationUsername": username}
    file_metadata_list = []
    for path, subdirs, files in os.walk(resource_main_dir):
        if not subdirs and not files:
            resources_ignored.append(path)
        for name in files:
            # Extract and encode the file bytes in the way expected by GitHub.
            file_bytes = open(os.path.join(path, name), 'rb').read()
            encoded_file = base64.b64encode(file_bytes).decode('utf-8')
            # A relative path to the file is what is added to the GitHub PUT address
            path_to_add = os.path.join(path.partition('/data/')[2], name)
            path_to_add_to_url = path_to_add.partition('/')[2].replace(' ', '_')
            finished_path = '/' + title + '/' + path_to_add_to_url
            file_metadata_list.append({
                "actionRootPath": os.path.join(path, name),
                "destinationPath": finished_path,
                "title": name,
                "destinationHash": None})

            put_url = "https://api.github.com/repos/{}/{}/contents/{}".format(
                username, title, path_to_add_to_url)
            data = {
                "message": "PresQT Upload",
                "committer": {
                    "name": "PresQT",
                    "email": "N/A"},
                "content": encoded_file}

            requests.put(put_url, headers=header, data=json.dumps(data))

    resources_updated = []

    return {
        'resources_ignored': resources_ignored,
        'resources_updated': resources_updated,
        'action_metadata': action_metadata,
        'file_metadata_list': file_metadata_list,
        'project_id': title
    }
