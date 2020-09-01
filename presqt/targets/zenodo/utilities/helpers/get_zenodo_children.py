

def zenodo_get_project_children(data, resource_id, is_record):
    """
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
