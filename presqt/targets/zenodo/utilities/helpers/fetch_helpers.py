

def zenodo_fetch_resources_helper(zenodo_projects, auth_parameter, is_record):
    """
    Takes a dictionary of Zenodo depositions/records and builds Zenodo PresQT resources.

    Parameters
    ----------
    zenodo_projects : dict
        The requesting user's Zenodo projects.
    auth_parameter : dict
        The user's Zenodo API token
    is_record : boolean
        Flag for if the resource is a published record

    Returns
    -------
        List of PresQT Zenodo Resources.
    """
    resources = []
    for entry in zenodo_projects:
        # This will determine if it's a record or a deposition
        if is_record is True:
            kind_name = entry['metadata']['resource_type']['type']
        else:
            kind_name = entry['metadata']['upload_type']
        resource = {
            "kind": "container",
            "kind_name": kind_name,
            "container": None,
            "id": entry['id'],
            "title": entry['metadata']['title']}
        resources.append(resource)

    return resources


def zenodo_fetch_resource_helper(zenodo_project, resource_id, is_record=False, is_file=False):
    """
    Takes a Zenodo deposition/record and builds a Zenodo PresQT resource.

    Parameters
    ----------
    zenodo_project : dict
        The requested Zenodo project.
    auth_parameter : dict
        The user's Zenodo API token
    is_record : boolean
        Flag for if the resource is a published record
    is_file : boolean
        Flag for if the resource is a file

    Returns
    -------
        PresQT Zenodo Resource (dict).
    """
    if is_file is False:
        if is_record is True:
            kind_name = zenodo_project['metadata']['resource_type']['type']
            date_modified = zenodo_project['updated']
        else:
            kind_name = zenodo_project['metadata']['upload_type']
            date_modified = zenodo_project['modified']

        kind = 'container'
        title = zenodo_project['metadata']['title']
        hashes = {}
        extra = {}
        for key, value in zenodo_project['metadata'].items():
            extra[key] = value

        from presqt.targets.zenodo.utilities.helpers.get_zenodo_children import zenodo_get_children
        children = zenodo_get_children(zenodo_project, resource_id, is_record)

    else:
        kind = 'item'
        kind_name = 'file'
        title = zenodo_project['key']
        date_modified = zenodo_project['updated']
        hashes = {'md5': zenodo_project['checksum'].partition(':')[2]}
        extra = {}
        children = []

    return {
        "kind": kind,
        "kind_name": kind_name,
        "id": resource_id,
        "title": title,
        "date_created": zenodo_project['created'],
        "date_modified": date_modified,
        "hashes": hashes,
        "extra": extra,
        "children": children}
