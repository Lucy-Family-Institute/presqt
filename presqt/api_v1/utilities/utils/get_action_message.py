def get_action_message(action, fixity_status, metadata_validation):
    # Fixity failed and metadata succeeded
    if not fixity_status and metadata_validation is True:
        return "{} succeeded but with fixity errors.".format(action)
    # Fixity failed and metadata failed
    elif not fixity_status and metadata_validation is not True:
        return "{} succeeded but with fixity and metadata errors.".format(action)
    # Fixity Succeeded and metadata failed
    elif fixity_status and metadata_validation is not True:
        return "{} succeeded but with metadata errors.".format(action)
    # Both Succeeded
    else:
        return "{} succeeded".format(action)
