import json

from presqt.json_schemas.schema_handlers import schema_validator


def create_download_metadata(instance, resource, fixity_obj):
    """
    Add metadata for a given resource to the list of file metadata.
    If the resource is a valid FTS metadata file, grab its contents and don't write metadata for it.

    Parameters
    ----------
    instance: BaseResource Class Instance
        Class instance we save metadata to.
    resource: Dict
        Resource dictionary we want metadata for.
    fixity_obj: Dict
        Dictionary of fixity information for this resource.

    Returns
    -------
    True if the resource is a valid FTS metadata file.
    False if the resource is not a valid FTS metadata file.
    """

    # If this is the PresQT FTS Metadata file, don't write it to disk but get its contents
    if resource['title'] == 'PRESQT_FTS_METADATA.json':
        source_fts_metadata_content = json.loads(resource['file'].decode())
        # If the metadata is valid then grab it's contents and don't save it
        if schema_validator('presqt/json_schemas/metadata_schema.json',
                            source_fts_metadata_content) is True:
            instance.source_fts_metadata_actions = instance.source_fts_metadata_actions + \
                                                   source_fts_metadata_content['actions']
            instance.all_keywords = instance.all_keywords + \
                                       source_fts_metadata_content['presqtKeywords']
            return True
        # If the metadata is invalid rename and write it. We don't want invalid contents.
        else:
            resource['path'] = resource['path'].replace('PRESQT_FTS_METADATA.json',
                                                        'INVALID_PRESQT_FTS_METADATA.json')
    metadata = {
        'destinationPath': resource['path'],
        'destinationHashes': {},
        'failedFixityInfo': [],
        'title': resource['title'],
        'sourceHashes': resource['hashes'],
        'sourcePath': resource['source_path'],
        'extra': resource['extra_metadata'],
    }
    # Add fixity info to metadata
    if not fixity_obj['fixity']:
        metadata['failedFixityInfo'].append(
            {
                'NewGeneratedHash': fixity_obj['presqt_hash'],
                'algorithmUsed': fixity_obj['hash_algorithm'],
                'reasonFixityFailed': fixity_obj['fixity_details']
            }
        )

    # Append file metadata to fts metadata list
    instance.new_fts_metadata_files.append(metadata)

    return False
