import requests

from presqt.utilities import update_process_info, increment_process_info


def get_figshare_project_data(initial_data, headers, resources, process_info_path):
    """
    Get all directories and files of given projects.

    Parameters
    ----------
    initial_data: list
        List of all top level projects
    headers: dict
        The authorization header that Figshare expects
    resources: list
        A list of resources to append to
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    A list of resources.
    """
    if process_info_path:
        # Add the total number of articles to the process info file.
        # This is necessary to keep track of the progress of the request.
        update_process_info(process_info_path, len(initial_data), 'resource_collection', 'fetch')

    for project in initial_data:
        resources.append({
            "kind": "container",
            "kind_name": "project",
            "container": None,
            "id": project['id'],
            "title": project['title']
        })
        # Increment the number of files done in the process info file.
        if process_info_path:
            increment_process_info(process_info_path, 'resource_collection', 'fetch')

    return resources


def get_search_project_data(initial_data, headers, resources, process_info_path):
    """
    Get all directories and files of a given project.

    Parameters
    ----------
    initial_data: list
        List of all top level projects
    headers: dict
        The authorization header that Figshare expects
    resources: list
        A list of resources to append to
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    A list of resources.
    """
    # Add the total number of articles to the process info file.
    # This is necessary to keep track of the progress of the request.
    if process_info_path:
        update_process_info(process_info_path, 1, 'resource_collection', 'fetch')

    resources.append({
        "kind": "container",
        "kind_name": "project",
        "container": None,
        "id": initial_data['id'],
        "title": initial_data['title']
    })
    # Increment the number of files done in the process info file.
    if process_info_path:
        increment_process_info(process_info_path, 'resource_collection', 'fetch')

    return resources
