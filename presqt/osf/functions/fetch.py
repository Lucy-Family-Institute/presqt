import requests

from presqt.osf.osf_classes.osf_file import OSFFile
from presqt.osf.osf_classes.osf_folder import OSFFolder
from presqt.osf.osf_classes.osf_node import OSFNode


def fetch_resources(token):
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
    # Get the user's nodes
    response = requests.get(
        'https://api.osf.io/v2/users/me/nodes/',
        headers={'Authorization': 'Bearer {}'.format(token)}
    )
    nodes = [node['id'] for node in response.json()['data']]

    assets = []
    for node in nodes:
        # Create node asset object
        osf_node = OSFNode('https://api.osf.io/v2/nodes/{}/'.format(node), token)
        node_obj = {
            'kind': 'container',
            'kind_name': 'project',
            'id': osf_node.id,
            'container': None,
            'title': osf_node.title
        }
        assets.append(node_obj)

        # For each storage provider within the current node,
        for storage in osf_node.get_storages:
            for asset in storage.get_assets_objects(OSFFile, OSFFolder, None):
                assets.append(asset)
    return assets