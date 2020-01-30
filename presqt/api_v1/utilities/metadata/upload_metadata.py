import os
from uuid import uuid4

from django.utils import timezone

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.utilities import get_dictionary_from_list, PresQTError, read_file


def get_upload_source_metadata(instance, bag):
    """
    Get all FTS metadata files in the bag. If they are valid then get their contents, otherwise
    rename the invalid metadata file.

    Parameters
    ----------
    instance: BaseResource class instance
        Class we want to add the attributes to
    bag: Bag Class instance
        The bag we want to traverse and update.
    """
    instance.source_fts_metadata_actions = []
    for bag_file in bag.payload_files():
        if os.path.split(bag_file)[-1] == 'PRESQT_FTS_METADATA.json':
            metadata_path = os.path.join(instance.resource_main_dir, bag_file)
            source_metadata_content = read_file(metadata_path, True)
            # If the FTS metadata is valid then remove it from the bag and save the actions.
            if schema_validator('presqt/json_schemas/metadata_schema.json',
                                source_metadata_content) is True:
                instance.source_fts_metadata_actions = instance.source_fts_metadata_actions + \
                    source_metadata_content['actions']
                os.remove(os.path.join(instance.resource_main_dir, bag_file))
                bag.save(manifests=True)
            # If the FTS metadata is invalid then rename the file in the bag.
            else:
                invalid_metadata_path = os.path.join(os.path.split(metadata_path)[0],
                                                     'INVALID_PRESQT_FTS_METADATA.json')
                os.rename(metadata_path, invalid_metadata_path)
                bag.save(manifests=True)


def create_upload_metadata(instance, file_metadata_list, action_metadata, project_id,
                           resources_ignored, resources_updated):
    """
    Create FTS file metadata for the action's resources.

    Parameters
    ----------
    instance: BaseResource Class Instance
        Class instance for the action
    file_metadata_list: list
        List of file metadata brought back from the upload function
    action_metadata: dict
        Metadata about the action itself
    project_id: str
        ID of the project the resource metadata should be uploaded to
    resources_ignored: list
        List of resource string paths that were ignored during upload
    resources_updated: list
        List of resource string paths that were updated during upload

    Returns
    -------
    Returns the result of schema validation against the final FTS metadata.
    Will be True if valid and an error string if invalid.
    """
    instance.action_metadata['destinationUsername'] = action_metadata['destinationUsername']

    # Put the file metadata in the correct file list
    instance.action_metadata['files'] = build_file_dict(instance.action_metadata['files']['created'],
                                                        resources_ignored, resources_updated,
                                                        'destinationPath')
    for resource in file_metadata_list:
        # Get the resource's metadata dict that has already been created
        fts_metadata_entry = get_dictionary_from_list(instance.new_fts_metadata_files,
                                                      'destinationPath',
                                                      resource['actionRootPath']
                                                      [len(instance.data_directory):])
        # Add destination metadata
        fts_metadata_entry['destinationHashes'] = {}
        if resource['destinationHash']:
            fts_metadata_entry['destinationHashes'][instance.hash_algorithm] = resource['destinationHash']

        fts_metadata_entry['destinationPath'] = resource['destinationPath']
        fts_metadata_entry['failedFixityInfo'] += resource['failed_fixity_info']

    # Create FTS metadata object
    from presqt.api_v1.utilities import create_fts_metadata
    fts_metadata_data = create_fts_metadata(instance.action_metadata,
                                            instance.source_fts_metadata_actions)
    # Write the metadata file to the destination target and validate the metadata file
    metadata_validation = write_and_validate_metadata(instance, project_id, fts_metadata_data)
    return metadata_validation


def write_and_validate_metadata(instance, project_id, fts_metadata_data):
    """
    Write FTS metadata to the correct place in the target's project. Also validate the FTS metadata.

    Parameters
    ----------
    instance: BaseResource Class Instance
        Class instance for the action
    project_id: str
        ID of the project the resource metadata should be uploaded to
    fts_metadata_data: dict
        Full FTS metadata to be written.

    Returns
    -------
    Returns the result of schema validation against the final FTS metadata.
    Will be True if valid and an error string if invalid.
    """
    from presqt.api_v1.utilities import FunctionRouter
    # Get the action's metadata upload function
    metadata_func = FunctionRouter.get_function(instance.destination_target_name, 'metadata_upload')

    try:
        metadata_func(instance.destination_token, project_id, fts_metadata_data)
    except PresQTError as e:
        # If the upload fails then return that error
        metadata_validation = e
    else:
        # If the upload succeeds then return the metadata's validation string
        metadata_validation = schema_validator('presqt/json_schemas/metadata_schema.json',
                                               fts_metadata_data)
    return metadata_validation


def build_file_dict(file_metadata, resources_ignored, resources_updated, path):
    """
    Add the metadata files to the correct file list.

    Parameters
    ----------
    file_metadata: list
        List of FTS file metadata.
    resources_ignored: list
        List of resource string paths that were ignored during upload
    resources_updated: list
        List of resource string paths that were updated during upload
    path: str
        The path in the metadata we want to look for in the resources lists

    Returns
    -------
    Dictionary of file lists.
    """
    files = {
        'created': [],
        'updated': [],
        'ignored': []
    }
    for metadata in file_metadata:
        if metadata[path] in resources_ignored:
            files['ignored'].append(metadata)
        elif metadata[path] in resources_updated:
            files['updated'].append(metadata)
        else:
            files['created'].append(metadata)
    return files
