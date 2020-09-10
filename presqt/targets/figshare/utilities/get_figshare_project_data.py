import requests

from presqt.utilities import update_process_info, increment_process_info


def get_figshare_project_data(initial_data, headers, resources):
    """
    Get all top level figshare projects.

    Parameters
    ----------
    initial_data: list
        List of all top level projects
    headers: dict
        The authorization header that Figshare expects
    resources: list
        A list of resources to append to

    Returns
    -------
    A list of resources.
    """
    for project in initial_data:
        resources.append({
            "kind": "container",
            "kind_name": "project",
            "container": None,
            "id": project['id'],
            "title": project['title']
        })

    return resources


def get_search_project_data(initial_data, headers, resources):
    """
    Get all top level figshare projects with search query.

    Parameters
    ----------
    initial_data: list
        List of all top level projects
    headers: dict
        The authorization header that Figshare expects
    resources: list
        A list of resources to append to

    Returns
    -------
    A list of resources.
    """
    resources.append({
        "kind": "container",
        "kind_name": "project",
        "container": None,
        "id": initial_data['id'],
        "title": initial_data['title']
    })

    return resources
