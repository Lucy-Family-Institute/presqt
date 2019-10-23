import json

from presqt.json_schemas.schema_handlers import schema_validator


def create_download_metadata(instance, resource, fixity_obj):
    # If this is the PresQT FTS Metadata file, don't write it to disk but get its contents
    if resource['title'] == 'PRESQT_FTS_METADATA.json':
        source_fts_metadata_content = json.loads(resource['file'].decode())
        # If the metadata is valid then grab it's contents and don't save it
        if schema_validator('presqt/json_schemas/metadata_schema.json', source_fts_metadata_content) is True:
            instance.source_fts_metadata_actions = instance.source_fts_metadata_actions + source_fts_metadata_content['actions']
            return True
        # If the metadata is invalid rename and write it. We don't want invalid contents.
        else:
            resource['path'] = resource['path'].replace('PRESQT_FTS_METADATA.json', 'INVALID_PRESQT_FTS_METADATA.json')

    # Add fixity info to metadata
    if not fixity_obj['fixity']:
        resource['metadata']['failedFixityInfo'] = [
            {'NewGeneratedHash': fixity_obj['presqt_hash'],
             'algorithmUsed': fixity_obj['hash_algorithm'],
             'reasonFixityFailed': fixity_obj['fixity_details']}]
    else:
        resource['metadata']['failedFixityInfo'] = []

    # Append file metadata to fts metadata list
    resource['metadata']['destinationPath'] = resource['path']
    resource['metadata']['destinationHashes'] = {}
    instance.new_fts_metadata_files.append(resource['metadata'])

    return False