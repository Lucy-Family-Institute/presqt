from presqt.osf.classes.main import OSF


def osf_download_resource(token, resource_id):
    """

    Parameters
    ----------
    token
    resource_id

    Returns
    -------

    """

    osf_instance = OSF(token)

    # Verify that it's a file