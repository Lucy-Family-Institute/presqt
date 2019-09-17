import os

from rest_framework import status

from presqt.targets.osf.utilities import get_osf_resource
from presqt.utilities import PresQTInvalidTokenError, PresQTResponseException
from presqt.targets.osf.classes.main import OSF


def osf_upload_resource(token, resource_id, resource_main_dir,
                        hash_algorithm, file_duplicate_action):
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
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    hashes = {}
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
                status.HTTP_400_BAD_REQUEST)
        elif resource.kind_name == 'project':
            hashes, files_ignored, files_updated = resource.storage('osfstorage').create_directory(
                resource_main_dir, file_duplicate_action, hashes, files_ignored, files_updated)
        else: # Folder or Storage
            hashes, files_ignored, files_updated = resource.create_directory(
                resource_main_dir, file_duplicate_action, hashes, files_ignored, files_updated)
    # else if we are uploading a new project
    else:
        os_path = next(os.walk(resource_main_dir))

        # Verify that the top level directory to upload only has one folder and no files.
        # This one folder will be the project title and the base for project upload.
        if len(os_path[1]) > 1:
            raise PresQTResponseException(
                'Project is not formatted correctly. Multiple directories exist at the top level.',
                status.HTTP_400_BAD_REQUEST)
        elif len(os_path[2]) > 0:
            raise PresQTResponseException(
                'Project is not formatted correctly. Files exist at the top level.',
                status.HTTP_400_BAD_REQUEST)

        # Get the actual data we want to upload
        data_to_upload_path = '{}/{}'.format(os_path[0], os_path[1][0])

        # Create a new project with the name being the top level directory's name.
        project = osf_instance.create_project(os_path[1][0])

        # Upload resources into OSFStorage for the new project.
        hashes, files_ignored, files_updated = project.storage('osfstorage').create_directory(
            data_to_upload_path, file_duplicate_action, hashes, files_ignored, files_updated)

    # Only send forward the hashes we need based on the hash_algorithm provided
    final_file_hashes = {}
    for key, value in hashes.items():
        final_file_hashes[key] = value[hash_algorithm]

    return final_file_hashes, files_ignored, files_updated
