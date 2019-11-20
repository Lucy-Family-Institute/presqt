import hashlib
import os
from uuid import uuid4

from django.utils import timezone
from rest_framework import status

from presqt.api_v1.utilities import create_fts_metadata, get_target_data, hash_generator
from presqt.utilities import zip_directory, PresQTResponseException, write_file, read_file


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
        zip_title = '{}.presqt.zip'.format(folders[0])
        zip_path = '/{}/{}'.format(folders[0], zip_title)
        # Make a new directory to contain the zip
        project_zip_path = os.path.join(zip_format_path, folders[0])
        os.mkdir(project_zip_path)

    except IndexError:
        # If not, we will zip up the file to be uploaded.
        zip_title = '{}.presqt.zip'.format(files[0])
        project_zip_path = zip_format_path
        zip_path = '/{}'.format(zip_title)


    # Write the metadata file into the data directory of the bag
    update_bagit_with_metadata(instance, zip_title)

    # Zip the file and store it in the created `zip_format/<title>` directory
    zip_directory(instance.resource_main_dir,
                  '{}/{}'.format(project_zip_path, zip_title),
                  instance.resource_main_dir)

    # Reset
    target_supported_algorithms = get_target_data(instance.destination_target_name)['supported_hash_algorithms']
    for hash_algorithm in target_supported_algorithms:
        if hash_algorithm in hashlib.algorithms_available:
            instance.hash_algorithm = hash_algorithm
            break
    else:
        instance.hash_algorithm = 'md5'

    # Since the metadata belonging with the files gets written inside of the zip,
    # Reset the metadata to associate with the zip file actually being uploaded
    zip_file = read_file('{}/{}'.format(project_zip_path, zip_title))
    zip_hash = hash_generator(zip_file, instance.hash_algorithm)
    instance.file_hashes = {'{}/{}'.format(project_zip_path, zip_title): zip_hash }

    instance.source_fts_metadata_actions = []
    instance.new_fts_metadata_files = [{
                'title': zip_title,
                'sourcePath': '/{}'.format(zip_title),
                'destinationPath': zip_path,
                'sourceHashes': {instance.hash_algorithm: zip_hash},
                'destinationHashes': {},
                'failedFixityInfo': [],
                'extra': {}
            }]

    instance.action_metadata = {
        'id': str(uuid4()),
        'actionDateTime': str(timezone.now()),
        'actionType': instance.action,
        'sourceTargetName': 'Server Created Zip',
        'sourceUsername': None,
        'destinationTargetName': instance.destination_target_name,
        'destinationUsername': None,
        'files': {
            'created': instance.new_fts_metadata_files,
            'updated': [],
            'ignored': []
        }
    }

    # Change the data directory to send to upload
    instance.data_directory = zip_format_path


def update_bagit_with_metadata(instance, zip_title):
    """
    Create a metadata file and resave and validate the bag.

    Parameters
    ----------
    instance : BaseResource class instance
        Class we want to add the attributes to
    zip_title: str
        Title of the zipped resource
    """
    for action_metadata in instance.action_metadata['files']['created']:
        action_metadata['destinationPath'] = '/{}/data{}'.format(zip_title, action_metadata['sourcePath'])
    instance.action_metadata['destinationTargetName'] = 'Zip File'

    final_fts_metadata_data = create_fts_metadata(instance.action_metadata,
                                                  instance.source_fts_metadata_actions)
    write_file(os.path.join(instance.data_directory, 'PRESQT_FTS_METADATA.json'),
               final_fts_metadata_data, True)

    # Update the bag
    instance.bag.save(manifests=True)
