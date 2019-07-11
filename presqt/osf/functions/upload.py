import os

from rest_framework import status

from presqt.exceptions import PresQTInvalidTokenError, PresQTResponseException
from presqt.osf.classes.main import OSF
from presqt.osf.helpers import get_osf_resource


def osf_upload_resource(token, resource_id, resource_main_dir,
                        hash_algorithm, file_duplicate_action):
    """
    Upload the files found in the resource_main_dir to the target.

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

    Returns
    -------
    final_file_hashes : dict
        Dictionary of file hashes obtained from the target
    files_ignored : array
        Array of file paths of files that were ignored when uploading the resource
    files_updated : array
        Array of file paths of files that were updated when uploading the resource
    """
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    file_hashes = {}
    files_ignored = []
    files_updated = []

    # If we are uploading to an existing container
    if resource_id:
        # Get the resource
        resource = get_osf_resource(resource_id, osf_instance)
        # Resource being uploaded to must not be a file
        if resource.kind_name == 'file':
            raise PresQTResponseException(
                "The Resource provided, {}, is not a container".format(resource_id),
                status.HTTP_401_UNAUTHORIZED)
        elif resource.kind_name == 'project':
            file_hashes, files_ignored, files_updated = resource.storage('osfstorage').create_directory(
                resource_main_dir,file_duplicate_action, file_hashes, files_ignored, files_updated)
        else:
            file_hashes, files_ignored, files_updated = resource.create_directory(
                resource_main_dir, file_duplicate_action, file_hashes, files_ignored, files_updated)
    # else if we are uploading a new project
    else:
        project = osf_instance.create_project(os.path.basename(resource_main_dir))
        file_hashes, files_ignored, files_updated = project.storage('osfstorage').create_directory(
            resource_main_dir, file_duplicate_action, file_hashes, files_ignored, files_updated)

    # Only send forward the hashes we need based on the hash_algorithm provided
    final_file_hashes = {}
    for key, value in file_hashes.items():
        final_file_hashes[key] = value[hash_algorithm]

    return final_file_hashes, files_ignored, files_updated