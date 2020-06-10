def create_fts_metadata(all_keywords, action_metadata, source_fts_metadata_actions):
    """
    Create an FTS metadata dictionary.

    Parameters
    ----------
    action_metadata: list
        List of action metadata for the current action.
    source_fts_metadata_actions: list
        List of action metadata for any actions found in the source.

    Returns
    -------
    Dictionary of FTS metadata.
    """
    return {
        'allKeywords': all_keywords,
        'actions':  [action_metadata] + source_fts_metadata_actions
    }
