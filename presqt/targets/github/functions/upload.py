import base64
import json
import os
import requests

from rest_framework import status

from presqt.targets.github.utilities import validation_check, create_repository
from presqt.utilities import PresQTResponseException


def github_upload_resource(token, resource_id, resource_main_dir,
                        hash_algorithm, file_duplicate_action):
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
    final_file_hashes : dict
        Dictionary of file hashes obtained from OSF calculated using the provided hash_algorithm.
        Key path must have the same base as resource_main_dir.
        Example:
        {
            'mediafiles/uploads/25/BagItToUpload/data/NewProj/funnyimages/Screen.png':
            '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141ea',
            'mediafiles/uploads/25/BagItToUpload/data/NewProj/funnyimages/Screen2.png':
            '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141eb',
         }
    files_ignored : array
        Array of string file paths of files that were ignored when uploading the resource.
        Path should have the same base as resource_main_dir.
        ['path/to/ignored/file.pg', 'another/ignored/file.jpg']

    files_updated : array
        Array of string file paths of files that were updated when uploading the resource.
        Path should have the same base as resource_main_dir.
        ['path/to/updated/file.jpg']
    """
    import datetime
    start = datetime.datetime.now()
    print("Starting beefy upload.")
    # Uploading to an existing Github repository is not allowed
    if resource_id:
        raise PresQTResponseException("Can't upload to an existing Github repository.",
                                      status.HTTP_400_BAD_REQUEST)

    try:
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException('The response returned a 401 unauthorized status code.',
                                      status.HTTP_401_UNAUTHORIZED)

    os_path = next(os.walk(resource_main_dir))

    # Verify that the top level directory to upload only has one folder and no files.
    # This one folder will be the project title and the base for project upload.
    if len(os_path[1]) > 1:
        raise PresQTResponseException(
            'Repository is not formatted correctly. Multiple directories exist at the top level.',
            status.HTTP_400_BAD_REQUEST)
    elif len(os_path[2]) > 0:
        raise PresQTResponseException(
            'Repository is not formatted correctly. Files exist at the top level.',
            status.HTTP_400_BAD_REQUEST)

    # Create a new repository with the name being the top level directory's name.
    # Note: GitHub doesn't allow spaces in repo_names
    repo_title = os_path[1][0].replace(' ', '_')
    create_repository(repo_title, token)
    resources_ignored = []
    file_dictionaries_list = []
    for path, subdirs, files in os.walk(resource_main_dir):
        if not subdirs and not files:
            resources_ignored.append(path)
        for name in files:
            # Extract and encode the file bytes in the way expected by GitHub.
            file_bytes = open(os.path.join(path, name), 'rb').read()
            encoded_file = base64.b64encode(file_bytes).decode('utf-8')
            # A relative path to the file is what is added to the GitHub PUT address
            path_to_add_to_url = os.path.join(path.partition('/data/')[2], name)

            file_dictionaries_list.append({
                "content": encoded_file,
                "url": "https://api.github.com/repos/{}/{}/contents/{}".format(
                    username, repo_title, path_to_add_to_url.partition('/')[2].replace(' ', '_'))})

    for file in file_dictionaries_list:
        put_content = {
            "message": "PresQT Transfer",
            "committer": {
                "name": "PresQT",
                "email": "N/A"},
            "content": file['content']}
        requests.put(file['url'], headers=header, data=json.dumps(put_content))

    # Github does not have hashes and we don't deal with file duplication because uploading to
    # an existing resource is not allowed.
    hashes = {}
    resources_updated = []
    print(datetime.datetime.now() - start)
    return hashes, resources_ignored, resources_updated