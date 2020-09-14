

def get_github_repository_data(initial_data, header, resources=[]):
    """
    Get's the repository data.

    Parameters
    ----------
    initial_data: list
        The initial data
    header: dict
        The gitHub authorization header
    resources: list
        The user's resources


    Returns
    -------
    The user's resources.
    """
    for repo in initial_data:
        resources.append({
            "kind": "container",
            "kind_name": "repo",
            "container": None,
            "id": repo["id"],
            "title": repo["name"]})

    return resources
