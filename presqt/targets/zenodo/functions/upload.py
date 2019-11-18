import os
import json
import requests

from rest_framework import status

from presqt.targets.utilities import get_duplicate_title
from presqt.targets.zenodo.utilities import zenodo_validation_check, zenodo_upload_helper
from presqt.utilities import PresQTValidationError, PresQTResponseException


def zenodo_upload_resource(token, resource_id, resource_main_dir, hash_algorithm,
                           file_duplicate_action):
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
    try:
        auth_parameter = zenodo_validation_check(token)
    except PresQTValidationError:
        raise PresQTValidationError("Zenodo returned a 401 unauthorized status code.", 401)

    os_path = next(os.walk(resource_main_dir))

    # Verify that the top level directory to upload only has one folder and no files.
    # This one folder will be the project title and the base for project upload.
    if len(os_path[1]) > 1:
        raise PresQTResponseException(
            "Repository is not formatted correctly. Multiple directories exist at the top level.",
            status.HTTP_400_BAD_REQUEST)

    if resource_id:
        name_helper = requests.get("https://zenodo.org/api/deposit/depositions/{}".format(
            resource_id), params=auth_parameter).json()

        try:
            project_title = name_helper['title']
        except KeyError:
            raise PresQTResponseException(
                "Can't find the resource with id {}, on Zenodo".format(resource_id),
                status.HTTP_404_NOT_FOUND)
        action_metadata = {"destinationUsername": None}
        post_url = "https://zenodo.org/api/deposit/depositions/{}/files".format(resource_id)

        upload_dict = zenodo_upload_loop(action_metadata, resource_id, resource_main_dir,
                                         post_url, auth_parameter, project_title)

    else:
        # Make sure if this is a new project, there are no files at the top level of the project.
        if len(os_path[2]) > 0:
            raise PresQTResponseException(
                "Repository is not formatted correctly. Files exist at the top level.",
                status.HTTP_400_BAD_REQUEST)

        action_metadata = {"destinationUsername": None}
        project_title = os_path[1][0]
        name_helper = requests.get("https://zenodo.org/api/deposit/depositions",
                                   params=auth_parameter).json()
        titles = [project['title'] for project in name_helper]
        new_title = get_duplicate_title(project_title, titles, ' (PresQT*)')
        resource_id = zenodo_upload_helper(auth_parameter, new_title)

        post_url = "https://zenodo.org/api/deposit/depositions/{}/files".format(resource_id)

        upload_dict = zenodo_upload_loop(action_metadata, resource_id, resource_main_dir,
                                         post_url, auth_parameter, new_title)

    return upload_dict


def zenodo_upload_loop(action_metadata, resource_id, resource_main_dir, post_url, auth_parameter,
                       title):
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
    file_metadata_list = []
    resources_updated = []
    action_metadata = {'destinationUsername': None}

    for path, subdirs, files in os.walk(resource_main_dir):
        if not subdirs and not files:
            resources_ignored.append(path)
        for name in files:
            data = {'name': name}
            files = {'file': open(os.path.join(path, name), "rb")}
            # Make the upload request....
            response = requests.post(post_url, params=auth_parameter,
                                     data=data, files=files)
            if response.status_code != 201:
                raise PresQTResponseException(
                    "Zenodo returned an error trying to upload {}".format(name),
                    status.HTTP_400_BAD_REQUEST)

            file_metadata_list.append({
                'actionRootPath': os.path.join(path, name),
                'destinationPath': '/{}/{}'.format(title, name),
                'title': name,
                'destinationHash': response.json()['checksum']})

    return {
        "resources_ignored": resources_ignored,
        "resources_updated": resources_updated,
        "action_metadata": action_metadata,
        "file_metadata_list": file_metadata_list,
        "project_id": resource_id,
    }
