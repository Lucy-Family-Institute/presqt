from presqt.osf.osf_classes.osf_main import OSF


def osf_fetch_resources(token):
    """
    Fetch all OSF assets (projects/nodes, folders, files) for the user connected
    to the given 'token'.

    Parameters
    ----------
    token : str
        User's OSF token

    Returns
    -------
    List of dictionary objects that represent an OSF asset.
    """

    osf_instance = OSF(token)
    assets = []
    osf_instance.get_user_assets(assets)

    return assets
