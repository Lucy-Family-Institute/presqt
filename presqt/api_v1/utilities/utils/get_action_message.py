def get_action_message(action, fixity_status, metadata_validation, action_metadata):
    """
    Get the final action message depending on the status of fixity and metadata.

    Parameters
    ----------
    action: str
        The action string to add to the message.
    fixity_status: Boolean
        Boolean flag for it any fixity failed during the action.
    metadata_validation: str/Boolean
        String of validation error or True boolean if metadata validation passed.
    action_metadata: dict
        Metadata for the PRESQT action.

    Returns
    -------
    Returns a string message.
    """
    from presqt.api_v1.utilities.utils.get_target_data import get_target_data

    new_file_list = (action_metadata['files']['created'] + action_metadata['files']['updated'] +
                     action_metadata['files']['ignored'])
    source_target_data = get_target_data(action_metadata['sourceTargetName'])
    destination_target_data = get_target_data(action_metadata['destinationTargetName'])

    for entry in new_file_list:
        if source_target_data and entry['sourceHashes'] == {} or set(
                entry['sourceHashes'].values()) == {None}:
            return "{} successful. Fixity failed because {} may not have provided a file checksum. See PRESQT_FTS_METADATA.json for more details.".format(
                action, source_target_data['readable_name'])
        if destination_target_data and entry['destinationHashes'] == {} or set(
                entry['destinationHashes'].values()) == {None}:
            return "{} successful. Fixity failed because {} may not have provided a file checksum. See PRESQT_FTS_METADATA.json for more details.".format(
                action, destination_target_data['readable_name'])

    # Fixity failed and metadata succeeded
    if not fixity_status and metadata_validation is True:
        return "{} successful but with fixity errors.".format(action)
    # Fixity failed and metadata failed
    elif not fixity_status and metadata_validation is not True:
        return "{} successful but with fixity and metadata errors.".format(action)
    # Fixity Succeeded and metadata failed
    elif fixity_status and metadata_validation is not True:
        return "{} successful but with metadata errors.".format(action)
    # Both Succeeded
    else:
        return "{} successful.".format(action)
