import requests

from presqt.utilities import update_process_info, increment_process_info


def zenodo_fetch_resources_helper(zenodo_projects, auth_parameter, is_record, process_info_path):
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
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
        List of PresQT Zenodo Resources.
    """
    # Add the total number of projects to the process info file.
    # This is necessary to keep track of the progress of the request.
    update_process_info(process_info_path, len(zenodo_projects), 'resource_collection', 'fetch')

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

        # # Now loop through the files
        # if is_record is True:
        #     # This will work on the records endpoint
        #     for item in entry['files']:
        #         resource = {
        #             "kind": "item",
        #             "kind_name": "file",
        #             "container": entry['id'],
        #             "id": item['bucket'],
        #             "title": item['key']}
        #         resources.append(resource)

        # Otherwise we need to pull the info from the depositions endpoint
        # else:
        #     for item in requests.get(entry['links']['files'], params=auth_parameter).json():
        #         resource = {
        #             "kind": "item",
        #             "kind_name": "file",
        #             "container": entry['id'],
        #             "id": item['id'],
        #             "title": item['filename']}
        #         resources.append(resource)
         # Increment the number of files done in the process info file.
        increment_process_info(process_info_path, 'resource_collection', 'fetch')

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

    else:
        kind = 'item'
        kind_name = 'file'
        title = zenodo_project['key']
        date_modified = zenodo_project['updated']
        hashes = {'md5': zenodo_project['checksum'].partition(':')[2]}
        extra = {}

    return {
        "kind": kind,
        "kind_name": kind_name,
        "id": resource_id,
        "title": title,
        "date_created": zenodo_project['created'],
        "date_modified": date_modified,
        "hashes": hashes,
        "extra": extra,
        "children": []}
