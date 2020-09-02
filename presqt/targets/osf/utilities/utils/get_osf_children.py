import requests


def get_osf_children(resource_id, token, parent_kind):
    """
    Get the children of the requested resource. Only going down one level.

    Parameters
    ----------
    resource_id : str
        The parent id of the children
    token : str
        The OSF API Token
    parent_kind : str
        The kind of the parent resource ['project', 'storage', or 'folder]
    
    Returns
    -------
        The children of the requested resource.
    """
    from presqt.targets.osf.utilities.utils.get_all_paginated_data import get_all_paginated_data

    headers = {"Authorization": "Bearer {}".format(token)}
    children = []

    split_id = resource_id.split(':')

    if parent_kind == 'project':
        # Get the project information
        data = requests.get(
            "https://api.osf.io/v2/nodes/{}/files".format(resource_id), headers=headers).json()

        for child in data['data']:
            children.append({
                "kind": "container",
                "kind_name": "storage",
                "container": resource_id,
                "id": child['id'],
                "title": child['attributes']['name']
            })

        # Also get the subprojects
        sub_data = requests.get(
            "https://api.osf.io/v2/nodes/{}/children".format(resource_id), headers=headers).json()

        for child in sub_data['data']:
            children.append({
                "kind": "container",
                "kind_name": "project",
                "container": resource_id,
                "id": child['id'],
                "title": child['attributes']['title']
            })

    elif parent_kind == 'storage':
        # Get the storage information
        data = get_all_paginated_data(
            "https://api.osf.io/v2/nodes/{}/files/{}".format(split_id[0], split_id[1]), token)

        for child in data:
            if child['attributes']['kind'] == 'folder':
                kind = 'container'
                kind_name = 'folder'
            else:
                kind = 'item'
                kind_name = 'file'

            children.append({
                "kind": kind,
                "kind_name": kind_name,
                "container": resource_id,
                "id": child['id'],
                "title": child['attributes']['name']
            })

    elif parent_kind == 'folder':
        # Get the folder information
        get_data_for_link = requests.get("https://api.osf.io/v2/files/{}".format(resource_id),
                                         headers=headers).json()
        data = get_all_paginated_data(
            get_data_for_link['data']['relationships']['files']['links']['related']['href'], token)

        for child in data:
            if child['attributes']['kind'] == 'folder':
                kind = 'container'
                kind_name = 'folder'
            else:
                kind = 'item'
                kind_name = 'file'

            children.append({
                "kind": kind,
                "kind_name": kind_name,
                "container": resource_id,
                "id": child['id'],
                "title": child['attributes']['name']
            })

    return children
