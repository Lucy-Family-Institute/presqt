import os
import json
import requests

from rest_framework import status

from presqt.targets.utilities import get_duplicate_title, upload_total_files
from presqt.targets.zenodo.utilities import zenodo_validation_check, zenodo_upload_helper
from presqt.utilities import (PresQTValidationError, PresQTResponseException,
                              update_process_info, increment_process_info, update_process_info_message)


def zenodo_upload_resource(token, resource_id, resource_main_dir, hash_algorithm,
                           file_duplicate_action, process_info_path, action):
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
        auth_parameter = zenodo_validation_check(token)
    except PresQTValidationError:
        raise PresQTValidationError("Token is invalid. Response returned a 401 status code.",
                                    status.HTTP_401_UNAUTHORIZED)

    os_path = next(os.walk(resource_main_dir))
    total_files = upload_total_files(resource_main_dir)
    # Update process info file
    update_process_info(process_info_path, total_files, action, 'upload')
    update_process_info_message(process_info_path, action, "Uploading files to Zenodo...")

    # Since Zenodo is a finite depth target, the checks for path validity have already been done.
    if resource_id:
        name_helper = requests.get("https://zenodo.org/api/deposit/depositions/{}".format(
            resource_id), params=auth_parameter).json()

        try:
            final_title = name_helper['title']
        except KeyError:
            raise PresQTResponseException(
                "Can't find the resource with id {}, on Zenodo".format(resource_id),
                status.HTTP_404_NOT_FOUND)
        action_metadata = {"destinationUsername": None}

    else:
        action_metadata = {"destinationUsername": None}
        project_title = os_path[1][0]
        name_helper = requests.get("https://zenodo.org/api/deposit/depositions",
                                   params=auth_parameter).json()
        titles = [project['title'] for project in name_helper]
        final_title = get_duplicate_title(project_title, titles, ' (PresQT*)')
        resource_id = zenodo_upload_helper(auth_parameter, final_title)

    post_url = "https://zenodo.org/api/deposit/depositions/{}/files".format(resource_id)
    upload_dict = zenodo_upload_loop(action_metadata, resource_id, resource_main_dir,
                                     post_url, auth_parameter, final_title, file_duplicate_action,
                                     process_info_path, action)

    return upload_dict


def zenodo_upload_loop(action_metadata, resource_id, resource_main_dir, post_url, auth_parameter,
                       title, file_duplicate_action, process_info_path, action):
    """
    Loop through the files to be uploaded and return the dictionary.

    Parameters
    ----------
    action_metadata : dict
        The metadata for this PresQT action
    resource_id : str
        The id of the resource the upload is happening on
    post_url : str
        The url to upload files to
    auth_parameter : dict
        Zenodo's authorization paramater
    title : str
        The title of the project created
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
    """
    resources_ignored = []
    resources_updated = []
    file_metadata_list = []
    action_metadata = {'destinationUsername': None}

    # Get current files associated with the resource.
    project_url = "https://zenodo.org/api/deposit/depositions/{}".format(resource_id)
    current_file_list = requests.get(project_url, params=auth_parameter).json()['files']
    file_title_list = [entry['filename'] for entry in current_file_list]

    for path, subdirs, files in os.walk(resource_main_dir):
        if not subdirs and not files:
            resources_ignored.append(path)

        for name in files:
            formatted_name = name.replace(' ', '_')
            if formatted_name in file_title_list and file_duplicate_action == 'ignore':
                resources_ignored.append(os.path.join(path, name))
                continue

            data = {'name': formatted_name}
            files = {'file': open(os.path.join(path, name), "rb")}

            if formatted_name in file_title_list and file_duplicate_action == 'update':
                # First we need to delete the old file
                for entry in current_file_list:
                    if formatted_name == entry['filename']:
                        delete_response = requests.delete(
                            entry['links']['self'], params=auth_parameter)
                        if delete_response.status_code != 204:
                            raise PresQTResponseException(
                                "Zenodo returned an error trying to update {}".format(name),
                                status.HTTP_400_BAD_REQUEST)
                        # Add this resource to the updated list
                        resources_updated.append(os.path.join(path, name))
            # Make the upload request....
            response = requests.post(post_url, params=auth_parameter,
                                     data=data, files=files)
            if response.status_code != 201:
                raise PresQTResponseException(
                    "Zenodo returned an error trying to upload {}".format(name),
                    status.HTTP_400_BAD_REQUEST)
            # Increment process info file
            increment_process_info(process_info_path, action, 'upload')

            file_metadata_list.append({
                'actionRootPath': os.path.join(path, name),
                'destinationPath': '/{}/{}'.format(title, formatted_name),
                'title': formatted_name,
                'destinationHash': response.json()['checksum']})

    return {
        "resources_ignored": resources_ignored,
        "resources_updated": resources_updated,
        "action_metadata": action_metadata,
        "file_metadata_list": file_metadata_list,
        "project_id": resource_id,
        "project_link": "https://zenodo.org/deposit?page=1&size=20"
    }
