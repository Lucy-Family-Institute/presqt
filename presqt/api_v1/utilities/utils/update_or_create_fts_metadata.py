def update_or_create_fts_metadata(action_metadata, presqt_fts_metadata_file_data):
    if presqt_fts_metadata_file_data:
        presqt_fts_metadata_file_data['actions'].append(action_metadata)
    else:
        presqt_fts_metadata_file_data['context'] = {
                "globus": "https://docs.globus.org/api/transfer/overview/",
        }
        presqt_fts_metadata_file_data['actions'] = action_metadata

    return presqt_fts_metadata_file_data