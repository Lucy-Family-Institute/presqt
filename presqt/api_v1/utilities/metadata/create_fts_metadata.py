def create_fts_metadata(all_keywords, action_metadata, source_fts_metadata_actions, extra_metadata):
    """
    Create an FTS metadata dictionary.

    Parameters
    ----------
    all_keywords: list
        List of all keywords associated with the resource
    action_metadata: list
        List of action metadata for the current action.
    source_fts_metadata_actions: list
        List of action metadata for any actions found in the source.
    extra_metadata: dict
        The extra metadata gathered during download

    Returns
    -------
    Dictionary of FTS metadata.
    """
    return {
        'allKeywords': all_keywords,
        'actions': [action_metadata] + source_fts_metadata_actions,
        'extra_metadata': extra_metadata
    }
