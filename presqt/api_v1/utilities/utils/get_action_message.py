def get_action_message(self, action, fixity_status, metadata_validation, action_metadata):
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

    new_file_list = (action_metadata['files']['created'] + action_metadata['files']['updated'])
    source_target_data = get_target_data(action_metadata['sourceTargetName'])
    destination_target_data = get_target_data(action_metadata['destinationTargetName'])

    # Determine if metadata or keyword failed
    error_list = []
    if not metadata_validation:
        error_list.append('metadata')
    if not self.keyword_enhancement_successful:
        error_list.append('keyword enhancement')

    for entry in new_file_list:
        # Check if the source or destination targets didn't provide checksums
        if source_target_data and entry['sourceHashes'] == {} or set( entry['sourceHashes'].values()) == {None}:
            no_fixity_target = source_target_data['readable_name']
        elif destination_target_data and entry['destinationHashes'] == {} or set(entry['destinationHashes'].values()) == {None}:
            no_fixity_target = destination_target_data['readable_name']
        else:
            no_fixity_target = None

        # If a target didn't provide checksums then return an error message that
        # accurately reflects all errors along with a fixity warning.
        if no_fixity_target:
            if error_list:
                return "{} successful but with {} errors. Fixity can't be determined because {} may not have provided a file checksum. See PRESQT_FTS_METADATA.json for more details.".format(
                    action, ', '.join(error_list), no_fixity_target)
            else:
                return "{} successful. Fixity can't be determined because {} may not have provided a file checksum. See PRESQT_FTS_METADATA.json for more details.".format(
                    action, no_fixity_target)

    if not fixity_status:
        error_list.append('fixity')

    if error_list:
        return '{} successful but with {} errors.'.format(action, ', '.join(error_list))
    else:
        return "{} successful.".format(action)
