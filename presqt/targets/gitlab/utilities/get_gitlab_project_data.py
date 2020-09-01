import urllib.parse

from presqt.utilities import update_process_info, increment_process_info


def get_gitlab_project_data(initial_data, headers, resources, process_info_path):
    """
    Get all directories and files of given projects.

    Parameters
    ----------
    initial_data: list
        List of all top level projects
    headers: dict
        The authorization header that GitLab expects
    resources: list
        A lis of resources to append to
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    A list of resources.

    """
    from presqt.targets.gitlab.utilities.gitlab_paginated_data import gitlab_paginated_data

    # Add the total number of projects to the process info file.
    # This is necessary to keep track of the progress of the request.
    update_process_info(process_info_path, len(initial_data), 'resource_collection', 'fetch')

    for project in initial_data:
        if ('marked_for_deletion_at' in project.keys() and not project['marked_for_deletion_at']) or (
                'marked_for_deletion_at' not in project.keys()):
            resources.append({
                "kind": "container",
                "kind_name": "project",
                "container": None,
                "id": project['id'],
                "title": project['name']})

            # Increment the number of files done in the process info file.
            increment_process_info(process_info_path, 'resource_collection', 'fetch')

    return resources
