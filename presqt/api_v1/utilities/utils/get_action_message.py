def get_action_message(action, fixity_status, metadata_validation):
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

    Returns
    -------
    Returns a string message.
    """
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
