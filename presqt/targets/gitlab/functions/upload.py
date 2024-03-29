import base64
import os

import requests
from rest_framework import status

from presqt.api_v1.utilities import hash_generator
from presqt.targets.gitlab.utilities import gitlab_paginated_data
from presqt.targets.gitlab.utilities.validation_check import validation_check
from presqt.targets.utilities import get_duplicate_title, upload_total_files
from presqt.utilities import PresQTResponseException, update_process_info, increment_process_info, update_process_info_message


def gitlab_upload_resource(token, resource_id, resource_main_dir, hash_algorithm, file_duplicate_action, process_info_path, action):
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
    base_url = "https://gitlab.com/api/v4/"

    try:
        headers, user_id = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    username = requests.get("https://gitlab.com/api/v4/user", headers=headers).json()['username']
    action_metadata = {"destinationUsername": username}

    os_path = next(os.walk(resource_main_dir))
    # Get total amount of files
    total_files = upload_total_files(resource_main_dir)
    update_process_info(process_info_path, total_files, action, 'upload')
    update_process_info_message(process_info_path, action,
                                "Uploading files to GitLab...")

    resources_ignored = []
    resources_updated = []
    file_metadata_list = []

    #*** CREATE NEW PROJECT ***#
    # Create a new project with the name being the top level directory's name.
    # Check if a project with this name exists for this user
    if not resource_id:
        project_title = os_path[1][0]
        titles = [data['name'] for data in gitlab_paginated_data(headers, user_id)]
        title = get_duplicate_title(project_title, titles,
                                    '-PresQT*-').replace('(', '-').replace(')', '-')
        response = requests.post('{}projects?name={}&visibility=public'.format(
            base_url, title), headers=headers)
        if response.status_code == 201:
            project_id = response.json()['id']
            project_name = response.json()['name']
            web_url = response.json()['web_url']
        else:
            raise PresQTResponseException(
                "Response has status code {} while creating project {}.".format(
                    response.status_code, project_title), status.HTTP_400_BAD_REQUEST)

        #*** UPLOAD FILES ***#
        # Upload files to project's repository
        base_repo_path = "{}projects/{}/repository/files/".format(base_url, project_id)
        for path, subdirs, files in os.walk(resource_main_dir):
            if not subdirs and not files:
                resources_ignored.append(path)
            for name in files:
                # Strip server directories from file path
                relative_file_path = os.path.join(path.partition('/data/{}/'.format(
                    project_title))[2], name)

                # Extract and encode the file bytes in the way expected by GitLab.
                file_bytes = open(os.path.join(path, name), 'rb').read()
                encoded_file = base64.b64encode(file_bytes)

                # A relative path to the file is what is added to the GitLab POST address
                encoded_file_path = relative_file_path.replace('/', '%2F').replace('.', '%2E')

                request_data = {"branch": "master",
                                "commit_message": "PresQT Upload",
                                "encoding": "base64",
                                "content": encoded_file}

                requests.post("{}{}".format(
                    base_repo_path, encoded_file_path), headers=headers, data=request_data)

                # Get the file hash
                file_json = requests.get("{}{}?ref=master".format(base_repo_path, encoded_file_path),
                                         headers=headers)
                # Increment files finished
                increment_process_info(process_info_path, action, 'upload')

                file_metadata_list.append({
                    "actionRootPath": os.path.join(path, name),
                    # This ensures that the title is up to date if there are duplicates
                    "destinationPath": os.path.join(project_name, path.partition(
                        '/data/')[2].partition('/')[2], name),
                    "title": name,
                    "destinationHash": file_json.json()['content_sha256']
                })
    else:
        if ':' not in resource_id:
            project_id = resource_id
            base_repo_url = "{}projects/{}/repository/files/".format(base_url, project_id)
            string_path_to_resource = ''
        else:
            partitioned_id = resource_id.partition(':')
            project_id = partitioned_id[0]
            base_repo_url = "{}projects/{}/repository/files/{}".format(
                base_url, project_id, partitioned_id[2])
            string_path_to_resource = partitioned_id[2].replace('%2F', '/').replace('%2E', '.')

        # Check if the resource_id belongs to a file
        tree_url = 'https://gitlab.com/api/v4/projects/{}/repository/tree?recursive=1'.format(
            project_id)
        file_data = gitlab_paginated_data(headers, None, tree_url)
        for data in file_data:
            if data['path'] == string_path_to_resource:
                if data['type'] == 'blob':
                    raise PresQTResponseException("Resource with id, {}, belongs to a file.".format(
                        resource_id), status.HTTP_400_BAD_REQUEST)

        # Get project data
        project = requests.get('{}projects/{}'.format(base_url, project_id), headers=headers)
        if project.status_code != 200:
            raise PresQTResponseException("Project with id, {}, could not be found.".format(
                project_id), status.HTTP_404_NOT_FOUND)
        project_name = project.json()['name']
        web_url = project.json()['web_url']

        for path, subdirs, files in os.walk(resource_main_dir):
            if not subdirs and not files:
                resources_ignored.append(path)
            for name in files:
                # Strip server directories from file path
                relative_file_path = os.path.join(path.partition('/data/')[2], name)

                # A relative path to the file is what is added to the GitLab POST address
                if base_repo_url == "{}projects/{}/repository/files/".format(base_url, project_id):
                    encoded_file_path = relative_file_path.replace('/', '%2F').replace('.', '%2E')
                else:
                    encoded_file_path = '%2F{}'.format(
                        relative_file_path.replace('/', '%2F').replace('.', '%2E'))
                full_encoded_url = '{}{}'.format(base_repo_url, encoded_file_path)

                ignore_file = False
                upload_request = requests.post
                file_bytes = None
                # Check if this file exists already
                for file in file_data:
                    if os.path.join(string_path_to_resource, relative_file_path) == file['path']:
                        if file_duplicate_action == 'ignore':
                            resources_ignored.append(os.path.join(path, name))
                            ignore_file = True
                            break
                        else:
                            file_url = '{}?ref=master'.format(full_encoded_url)
                            file_response = requests.get(file_url, headers=headers)
                            file_bytes = open(os.path.join(path, name), 'rb').read()
                            if hash_generator(file_bytes, 'sha256') == file_response.json()['content_sha256']:
                                resources_ignored.append(os.path.join(path, name))
                                ignore_file = True
                            else:
                                resources_updated.append(os.path.join(path, name))
                                upload_request = requests.put

                            # Break out of this for loop and attempt to upload this duplicate
                            break
                # If we find a file to ignore then move onto the next file in the os.walk
                if ignore_file:
                    continue

                # Extract and encode the file bytes in the way expected by GitLab.
                if not file_bytes:
                    file_bytes = open(os.path.join(path, name), 'rb').read()
                encoded_file = base64.b64encode(file_bytes)

                request_data = {"branch": "master",
                                "commit_message": "PresQT Upload",
                                "encoding": "base64",
                                "content": encoded_file}

                response = upload_request("{}".format(full_encoded_url),
                                          headers=headers, data=request_data)
                if response.status_code not in [201, 200]:
                    raise PresQTResponseException(
                        'Upload failed with a status code of {}'.format(response.status_code),
                        status.HTTP_400_BAD_REQUEST)

                # Get the file hash
                file_json = requests.get("{}?ref=master".format(full_encoded_url),
                                         headers=headers).json()
                # Increment files finished
                increment_process_info(process_info_path, action, 'upload')

                file_metadata_list.append({
                    "actionRootPath": os.path.join(path, name),
                    "destinationPath": os.path.join(project_name, path.partition('/data/')[2], name),
                    "title": name,
                    "destinationHash": file_json['content_sha256']
                })

    return {
        'resources_ignored': resources_ignored,
        'resources_updated': resources_updated,
        'action_metadata': action_metadata,
        'file_metadata_list': file_metadata_list,
        'project_id': project_id,
        'project_link': web_url
    }
