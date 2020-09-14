import os
import requests

from rest_framework import status

from presqt.targets.osf.utilities import get_osf_resource
from presqt.utilities import (
    PresQTInvalidTokenError, PresQTResponseException, update_process_info,
    update_process_info_message)
from presqt.targets.osf.classes.main import OSF
from presqt.targets.utilities import upload_total_files


def osf_upload_resource(token, resource_id, resource_main_dir,
                        hash_algorithm, file_duplicate_action,
                        process_info_path, action):
    """
    Upload the files found in the resource_main_dir to OSF.

    Parameters
    ----------
    token : str
        User's OSF token.
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
        'action_metadata': Dictionary containing FTS action metadata. Must be in the following format:
                            {
                                'destinationUsername': 'some_username'
                            }
        'file_metadata_list': List of dictionaries for each file that contains FTS metadata
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
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    # Get contributor name
    contributor_name = requests.get('https://api.osf.io/v2/users/me/',
                                    headers={'Authorization': 'Bearer {}'.format(token)}).json()[
                                        'data']['attributes']['full_name']
    action_metadata = {"destinationUsername": contributor_name}

    hashes = {}
    resources_ignored = []
    resources_updated = []
    file_metadata_list = []
    # Get total amount of files
    total_files = upload_total_files(resource_main_dir)
    update_process_info(process_info_path, total_files, action, 'upload')
    update_process_info_message(process_info_path, action, "Uploading files to OSF...")

    # If we are uploading to an existing container
    if resource_id:
        # Get the resource
        resource = get_osf_resource(resource_id, osf_instance)

        # Resource being uploaded to must not be a file
        if resource.kind_name == 'file':
            raise PresQTResponseException(
                "The Resource provided, {}, is not a container".format(resource_id),
                status.HTTP_400_BAD_REQUEST)

        elif resource.kind_name == 'project':
            project = resource
            project_id = project.id
            resource.storage('osfstorage').create_directory(
                resource_main_dir, file_duplicate_action, hashes,
                resources_ignored, resources_updated, file_metadata_list, process_info_path, action)

        else:  # Folder or Storage
            resource.create_directory(
                resource_main_dir, file_duplicate_action, hashes,
                resources_ignored, resources_updated, file_metadata_list, process_info_path, action)
            # Get the project class for later metadata work
            if resource.kind_name == 'storage':
                project_id = resource.node
            else:
                project_id = resource.parent_project_id
            project = osf_instance.project(project_id)

    # else we are uploading a new project
    else:
        os_path = next(os.walk(resource_main_dir))

        # Get the actual data we want to upload
        data_to_upload_path = '{}/{}'.format(os_path[0], os_path[1][0])

        # Create a new project with the name being the top level directory's name.
        project = osf_instance.create_project(os_path[1][0])
        project_id = project.id

        # Upload resources into OSFStorage for the new project.
        project.storage('osfstorage').create_directory(
            data_to_upload_path, file_duplicate_action, hashes,
            resources_ignored, resources_updated, file_metadata_list, process_info_path, action)

    for file_metadata in file_metadata_list:
        # Only send forward the hash we need based on the hash_algorithm provided
        file_metadata['destinationHash'] = file_metadata['destinationHash'][hash_algorithm]
        # Prepend the project title to each resource's the metadata destinationPath
        file_metadata['destinationPath'] = '/{}/{}'.format(
            project.title, file_metadata['destinationPath'])

    return {
        'resources_ignored': resources_ignored,
        'resources_updated': resources_updated,
        'action_metadata': action_metadata,
        'file_metadata_list': file_metadata_list,
        'project_id': project_id
    }
