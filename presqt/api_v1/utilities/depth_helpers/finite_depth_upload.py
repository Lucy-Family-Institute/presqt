import os

from rest_framework import status

from presqt.api_v1.utilities import create_fts_metadata
from presqt.utilities import zip_directory, PresQTResponseException, write_file


def finite_depth_upload_helper(instance):
    """
    This function will run if an upload has a destination of finite depth. It's purpose is to zip up
    the contents of whatever is being uploaded.

    Parameters
    ----------
    instance: BaseResource class instance
        Class we want to add the attributes to
    """
    # Get information about the data directory
    os_path, folders, files = next(os.walk(instance.data_directory))

    if len(folders) > 1:
        raise PresQTResponseException(
            "Repository is not formatted correctly. Multiple directories exist at the top level.",
            status.HTTP_400_BAD_REQUEST)

    if len(files) > 0 and instance.destination_resource_id is None:
        raise PresQTResponseException(
            "Repository is not formatted correctly. Files exist at the top level.",
            status.HTTP_400_BAD_REQUEST)

    # Make a directory to store the zipped items
    zip_format_path = os.path.join(instance.ticket_path, 'zip_format')
    os.mkdir(zip_format_path)

    try:
        # Check to see if this is a project.
        project_title = folders[0]

    except IndexError:
        # If not, we will zip up the file to be uploaded.
        file_title = files[0]

        # Call bag func
        update_bagit_with_metadata(instance)
        # Zip the file and store it in the created `zip_format` directory
        zip_directory(instance.ticket_path,
                      '{}/{}.presqt.zip'.format(zip_format_path, file_title),
                      instance.ticket_path)

    else:
        update_bagit_with_metadata(instance)
        # Otherwise the whole directory needs to be zipped
        # Make a new directory to contain the zip
        project_zip_path = os.path.join(zip_format_path, project_title)
        os.mkdir(project_zip_path)

        # Zip the file and store it in the created `zip_format/<project_title>` directory
        zip_directory(instance.resource_main_dir,
                      '{}/{}.presqt.zip'.format(project_zip_path, project_title),
                      instance.resource_main_dir)

    # Change the data directory to send to upload
    instance.data_directory = zip_format_path


def update_bagit_with_metadata(instance):
    """
    Create a metadata file and resave and validate the bag.

    Parameters
    ----------
    instance : BaseResource class instance
        Class we want to add the attributes to
    """
    if instance.action != 'resource_upload':
        print('Shouldnt see this')
        final_fts_metadata_data = create_fts_metadata(instance.action_metadata,
                                                      instance.source_fts_metadata_actions)
        write_file(os.path.join(instance.data_directory, 'PRESQT_FTS_METADATA.json'),
                   final_fts_metadata_data, True)

        # Update the bag
        instance.bag.save(manifests=True)
