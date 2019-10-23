def create_fts_metadata(action_metadata, source_fts_metadata_actions):
    current_action_metadata = [action_metadata]
    return {
        'context': {
            'globus': "https://docs.globus.org/api/transfer/overview/"
        },
        'actions':  current_action_metadata + source_fts_metadata_actions
    }
