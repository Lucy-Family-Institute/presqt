from uuid import uuid4

from django.utils import timezone

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.utilities import get_dictionary_from_list, PresQTError


def create_upload_transfer_metadata(instance, action_metadata, file_metadata_list, data_directory, project_id, resources_ignored, resources_updated):
    instance.process_info_obj['upload_status'] = instance.process_info_obj['message']
    instance.action_metadata['destinationUsername'] = action_metadata['destinationUsername']

    files = {
        'created': [],
        'updated': [],
        'ignored': []
    }
    for metadata in instance.action_metadata['files']['created']:
        if metadata['destinationPath'] in resources_ignored:
            files['ignored'].append(metadata)
        elif metadata['destinationPath'] in resources_updated:
            files['updated'].append(metadata)
        else:
            files['created'].append(metadata)
    instance.action_metadata['files'] = files

    for resource in file_metadata_list:
        resource_hash = {}
        if resource['destinationHash']:
            resource_hash[instance.hash_algorithm] = resource['destinationHash']
        fts_metadata_entry = get_dictionary_from_list(instance.new_fts_metadata_files,
                                                      'destinationPath',
                                                      resource['actionRootPath']
                                                      [len(data_directory):])
        fts_metadata_entry['destinationHashes'] = resource_hash
        fts_metadata_entry['destinationPath'] = resource['destinationPath']
        if resource['failed_fixity_info']:
            fts_metadata_entry['failedFixityInfo'].append(resource['failed_fixity_info'])



    from presqt.api_v1.utilities import create_fts_metadata
    fts_metadata_data = create_fts_metadata(instance.action_metadata, instance.source_fts_metadata_actions)
    metadata_validation = write_and_validate_metadata(instance, data_directory, project_id,
                                                      fts_metadata_data)
    return metadata_validation

def create_upload_metadata(instance, file_metadata_list, data_directory, action_metadata, project_id, resources_ignored, resources_updated):
    fts_metadata = []
    for resource in file_metadata_list:
        resource_hash = None
        if resource['destinationHash']:
            resource_hash = {instance.hash_algorithm: resource['destinationHash']}
        fts_metadata.append({
            'title': resource['title'],
            'sourcePath': resource['actionRootPath'][len(data_directory):],
            'destinationPath': resource['destinationPath'],
            'sourceHashes': {instance.hash_algorithm: instance.file_hashes[resource['actionRootPath']]},
            'destinationHashes': resource_hash,
            'failedFixityInfo': resource['failed_fixity_info'],
            'extra': {}
        })

    files = {
        'created':  [],
        'updated': [],
        'ignored': []
    }
    print(resources_ignored)
    print(resources_updated)
    for metadata in fts_metadata:
        print(metadata['sourcePath'])
        if metadata['sourcePath'] in resources_ignored:
            files['ignored'].append(metadata)
        elif metadata['sourcePath'] in resources_updated:
            files['updated'].append(metadata)
        else:
            files['created'].append(metadata)

    action_metadata = {
        'id': str(uuid4()),
        'actionDateTime': str(timezone.now()),
        'actionType': instance.action,
        'sourceTargetName': 'Local Machine',
        'destinationTargetName': instance.destination_target_name,
        'sourceUsername': None,
        'destinationUsername': action_metadata['destinationUsername'],
        'files': files
    }

    from presqt.api_v1.utilities import create_fts_metadata
    fts_metadata_data = create_fts_metadata(action_metadata, instance.source_metadata_actions)
    metadata_validation = write_and_validate_metadata(instance, data_directory, project_id, fts_metadata_data)
    return metadata_validation

def write_and_validate_metadata(instance, data_directory, project_id, fts_metadata_data):
    from presqt.api_v1.utilities import FunctionRouter
    metadata_func = FunctionRouter.get_function(instance.destination_target_name, 'metadata_upload')

    try:
        metadata_func(instance.destination_token, instance.destination_resource_id, data_directory,
                      fts_metadata_data, project_id)
    except PresQTError as e:
        metadata_validation = e
    else:
        # Validate the final metadata
        metadata_validation = schema_validator('presqt/json_schemas/metadata_schema.json',
                                               fts_metadata_data)
    return metadata_validation


