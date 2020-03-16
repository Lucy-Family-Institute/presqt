from presqt.utilities import read_file


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
    targets_data = read_file('presqt/targets.json', True)

    for data in targets_data:
        if data['name'] == action_metadata['sourceTargetName']:
            if data['supported_hash_algorithms'] == []:
                return "{} successful. Fixity failed because {} does not provide file checksums.".format(
                    action, action_metadata['sourceTargetName'])
        elif data['name'] == action_metadata['destinationTargetName']:
            if data['supported_hash_algorithms'] == []:
                return "{} successful. Fixity failed because {} does not provide file checksums.".format(
                    action, action_metadata['destinationTargetName'])

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
