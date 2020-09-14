

def zenodo_get_children(data, resource_id, is_record):
    """
    Get the children of the requested resource. Only going down one level.

    Parameters
    ----------
    data : dict
        The project path data
    resource_id : str
        The resource id of the children
    is_record :  bool
        Is this a Zenodo record or deposition

    Returns
    -------
        The children of the requested resource.
    """
    children = []

    for child in data['files']:
        # Records and depositions have different keys..
        if is_record is True:
            id = child['bucket']
            title = child['key']
        else:
            id = child['id']
            title = child['filename']

        children.append({
            "kind": "item",
            "kind_name": "file",
            "container": resource_id,
            "id": id,
            "title": title
        })

    return children
