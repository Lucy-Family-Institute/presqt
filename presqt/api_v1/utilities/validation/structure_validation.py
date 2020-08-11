import os

from rest_framework import status

from presqt.utilities import PresQTResponseException


def structure_validation(instance):
    """
    This function will ensure that the structure of the files or project to upload are valid.

    Parameters
    ----------
    instance: BaseResource class instance
        Class we want to add the attributes to
    """
    # Get information about the data directory
    os_path, folders, files = next(os.walk(instance.data_directory))

    if len(folders) > 1:
        raise PresQTResponseException(
            "PresQT Error: Repository is not formatted correctly. Multiple directories exist at the top level.",
            status.HTTP_400_BAD_REQUEST)

    if len(files) > 0 and instance.destination_resource_id is None and instance.action == 'resource_upload':
        raise PresQTResponseException(
            "PresQT Error: Repository is not formatted correctly.",
            status.HTTP_400_BAD_REQUEST)

    if len(files) > 0 and instance.destination_resource_id is None and instance.action == 'resource_transfer_in':
        raise PresQTResponseException(
            "PresQT Error: You need to select a resource to transfer into, as a single file can not be uploaded as a new project.",
            status.HTTP_400_BAD_REQUEST)