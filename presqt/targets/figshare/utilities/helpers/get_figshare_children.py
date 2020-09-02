

def get_figshare_project_children(data, resource_id, kind_name):
    """
    Get the children of the requested resource. Only going down one level.

    Parameters
    ----------
    data : list
        The project or article path data
    resource_id : str
        The requested resource id
    kind_name :  str
        The kind we are  looking to build

    Returns
    -------
        The children of the requested resource.
    """
    children = []

    for child in data:
        if kind_name == 'article':
            kind = 'container'
            title = child['title']
        else:
            kind = 'file'
            title = child['name']

        children.append({
            "kind": kind,
            "kind_name": kind_name,
            "container": resource_id,
            "id": "{}:{}".format(resource_id, child['id']),
            "title": title
        })

    return children
