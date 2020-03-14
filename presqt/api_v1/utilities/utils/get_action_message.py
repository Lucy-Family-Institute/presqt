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
    if action != 'Download':
        # Make a combined list of the file lists.
        new_file_list = (action_metadata['files']['created'] + action_metadata['files']['updated'] +
                         action_metadata['files']['ignored'])
        total_file_count = len(new_file_list)

        hashless_destination_files = 0
        hashless_source_files = 0

        for entry in new_file_list:
            if entry['destinationHashes'] == {}:
                hashless_destination_files += 1
            if entry['sourceHashes'] == {}:
                hashless_source_files += 1

        if hashless_destination_files == total_file_count:
            return "{} successful. Fixity failed because {} does not provide file checksums.".format(
                action, action_metadata['destinationTargetName'])
        if hashless_source_files == total_file_count:
            return "{} successful. Fixity failed because {} does not provide file checksums.".format(
                action, action_metadata['sourceTargetName'])

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
