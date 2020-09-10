

def get_gitlab_project_data(initial_data, headers, resources):
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
    for project in initial_data:
        if ('marked_for_deletion_at' in project.keys() and not project['marked_for_deletion_at']) or (
                'marked_for_deletion_at' not in project.keys()):
            resources.append({
                "kind": "container",
                "kind_name": "project",
                "container": None,
                "id": project['id'],
                "title": project['name']})

    return resources
