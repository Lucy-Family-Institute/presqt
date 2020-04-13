import urllib.parse
import requests


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
        The user's rersources.

    Returns
    -------
    The user's resources.
    """
    for repo in initial_data:
        get_contents = requests.get(repo['contents_url'].partition('{')[0], headers=header).json()
        resource = {
            "kind": "container",
            "kind_name": "repo",
            "container": None,
            "id": repo["id"],
            "title": repo["name"]}
        resources.append(resource)

        if isinstance(get_contents, list):
            get_github_file_data(repo['id'], repo['id'], get_contents, header, resources)
    return resources


def get_github_file_data(parent_id, repo_id, contents, header, resources):
    """
    Get's the repository's file data.

    Parameters
    ----------
    parent_id: str
        The id of the parent item
    initial_data: list
        The initial data
    header: dict
        The gitHub authorization header
    resources: list
        The user's resources.

    Returns
    -------
    The user's resources.
    """
    for item in contents:
        if item['type'] == 'file':
            resource = {
                "kind": "item",
                "kind_name": "file",
                "container": parent_id,
                "id": "{}:{}".format(repo_id, urllib.parse.quote_plus(item['path']).replace(".", "%2E")),
                "title": item["name"]}
            resources.append(resource)

        elif item['type'] == 'dir':
            dir_id = "{}:{}".format(repo_id, urllib.parse.quote_plus(item['path']).replace(".", "%2E"))
            resource = {
                "kind": "container",
                "kind_name": "dir",
                "container": parent_id,
                "id": dir_id,
                "title": item["name"]}
            resources.append(resource)
            contents = requests.get(item['url'], headers=header).json()
            get_github_file_data(dir_id, repo_id, contents, header, resources)
    return resources
