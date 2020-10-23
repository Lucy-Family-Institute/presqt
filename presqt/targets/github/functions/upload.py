import base64
import json
import os
import requests

from rest_framework import status

from presqt.targets.github.utilities import validation_check, create_repository
from presqt.utilities import PresQTResponseException, update_process_info, increment_process_info, update_process_info_message
from presqt.targets.utilities import upload_total_files


def github_upload_resource(token, resource_id, resource_main_dir, hash_algorithm, file_duplicate_action, process_info_path, action):
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
    process_info_path: str
        Path to the process info file that keeps track of the action's progress
    action: str
        The action being performed

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
        'project_link': The link to either the resource or the home page of the user if not available through API
    """
    try:
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    os_path = next(os.walk(resource_main_dir))
    # Get total amount of files
    total_files = upload_total_files(resource_main_dir)
    update_process_info(process_info_path, total_files, action, 'upload')
    update_process_info_message(process_info_path, action, "Uploading files to GitHub...")

    # Upload a new repository
    if not resource_id:
        # Create a new repository with the name being the top level directory's name.
        # Note: GitHub doesn't allow spaces, or circlebois in repo_names
        repo_title = os_path[1][0].replace(' ', '_').replace("(", "-").replace(")", "-")
        repo_name, repo_id, repo_url = create_repository(repo_title, token)

        resources_ignored = []
        resources_updated = []
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
                finished_path = '/' + repo_name + '/' + path_to_add_to_url
                file_metadata_list.append({
                    "actionRootPath": os.path.join(path, name),
                    "destinationPath": finished_path,
                    "title": name,
                    "destinationHash": None})

                put_url = "https://api.github.com/repos/{}/{}/contents/{}".format(
                    username, repo_name, path_to_add_to_url)
                data = {
                    "message": "PresQT Upload",
                    "committer": {
                        "name": "PresQT",
                        "email": "N/A"},
                    "content": encoded_file}

                requests.put(put_url, headers=header, data=json.dumps(data))
                # Increment the file counter
                increment_process_info(process_info_path, action, 'upload')
    else:
        # Upload to an existing repository
        if ':' not in resource_id:
            repo_id = resource_id
            path_to_upload_to = ''
        # Upload to an existing directory
        else:
            partitioned_id = resource_id.partition(':')
            repo_id = partitioned_id[0]
            path_to_upload_to = '/{}'.format(partitioned_id[2]
                                             ).replace('%2F', '/').replace('%2E', '.')

        # Get initial repo data for the resource requested
        repo_url = 'https://api.github.com/repositories/{}'.format(repo_id)
        response = requests.get(repo_url, headers=header)

        if response.status_code != 200:
            raise PresQTResponseException(
                'The resource with id, {}, does not exist for this user.'.format(resource_id),
                status.HTTP_404_NOT_FOUND)
        repo_data = response.json()
        repo_name = repo_data['name']
        repo_url = repo_data['svn_url']

        # Get all repo resources so we can check if any files already exist
        repo_resources = requests.get(
            '{}/master?recursive=1'.format(repo_data['trees_url'][:-6]), headers=header).json()
        if 'message' in repo_resources:
            repo_resources = requests.get(
                '{}/main?recursive=1'.format(repo_data['trees_url'][:-6]), headers=header).json()
        # current_file_paths = ['/' + resource['path'] for resource in repo_resources['tree'] if resource['type'] == 'blob']
        current_file_paths = []
        for resource in repo_resources['tree']:
            if resource['type'] == 'blob':
                current_file_paths.append('/' + resource['path'])

        # Check if the provided path to upload to is actually a path to an existing file
        if path_to_upload_to in current_file_paths:
            raise PresQTResponseException(
                'The Resource provided, {}, is not a container'.format(resource_id),
                status.HTTP_400_BAD_REQUEST)

        resources_ignored = []
        resources_updated = []
        file_metadata_list = []
        sha = None
        action_metadata = {"destinationUsername": username}

        for path, subdirs, files in os.walk(resource_main_dir):
            if not subdirs and not files:
                resources_ignored.append(path)
            for name in files:
                path_to_file = os.path.join('/', path.partition('/data/')
                                            [2], name).replace(' ', '_')

                # Check if the file already exists in this repository
                full_file_path = '{}{}'.format(path_to_upload_to, path_to_file)
                if full_file_path in current_file_paths:
                    if file_duplicate_action == 'ignore':
                        resources_ignored.append(os.path.join(path, name))
                        continue
                    else:
                        resources_updated.append(os.path.join(path, name))
                        # Get the sha
                        sha_url = 'https://api.github.com/repos/{}/contents{}'.format(
                            repo_data['full_name'], full_file_path)
                        sha_response = requests.get(sha_url, headers=header)
                        sha = sha_response.json()['sha']

                # Extract and encode the file bytes in the way expected by GitHub.
                file_bytes = open(os.path.join(path, name), 'rb').read()
                encoded_file = base64.b64encode(file_bytes).decode('utf-8')
                # A relative path to the file is what is added to the GitHub PUT address
                file_metadata_list.append({
                    "actionRootPath": os.path.join(path, name),
                    "destinationPath": '/{}{}{}'.format(repo_name, path_to_upload_to, path_to_file),
                    "title": name,
                    "destinationHash": None})
                put_url = 'https://api.github.com/repos/{}/contents{}{}'.format(
                    repo_data['full_name'], path_to_upload_to, path_to_file)

                data = {
                    "message": "PresQT Upload",
                    "sha": sha,
                    "committer": {
                        "name": "PresQT",
                        "email": "N/A"},
                    "content": encoded_file}

                upload_response = requests.put(put_url, headers=header, data=json.dumps(data))

                if upload_response.status_code not in [200, 201]:
                    raise PresQTResponseException(
                        'Upload failed with a status code of {}'.format(
                            upload_response.status_code),
                        status.HTTP_400_BAD_REQUEST)
                # Increment the file counter
                increment_process_info(process_info_path, action, 'upload')

    return {
        'resources_ignored': resources_ignored,
        'resources_updated': resources_updated,
        'action_metadata': action_metadata,
        'file_metadata_list': file_metadata_list,
        'project_id': repo_id,
        "project_link": repo_url
    }
