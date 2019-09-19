import json
import os

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
    # Uploading to an existing Github repository is not allowed
    if resource_id:
        raise PresQTResponseException("Can't upload to an existing Github repository.",
                                      status.HTTP_400_BAD_REQUEST)

    try:
        username, header = validation_check(token)
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

    # Get the actual data we want to upload
    data_to_upload_path = '{}/{}'.format(os_path[0], os_path[1][0])

    # Create a new repository with the name being the top level directory's name.
    repository_json = create_repository(os_path[1][0], token)

    print(json.dumps(repository_json))

    # Github does not have hashes and we don't deal with file duplication because uploading to
    # an existing resource is not allowed.
    hashes = {}
    files_ignored = []
    files_updated = []

    return hashes, files_ignored, files_updated