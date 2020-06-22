import requests


def get_figshare_project_data(initial_data, headers, resources):
    """
    Get all directories and files of given projects.

    Parameters
    ----------
    initial_data: list
        List of all top level projects
    headers: dict
        The authorizaion header that Figshare expects
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
        file_get = requests.get("https://api.figshare.com/v2/account/projects/{}/articles".format(
            project['id']), headers=headers).json()

        for file in file_get:
            resources.append({
                "kind": "item",
                "kind_name": file["defined_type_name"],
                "container": project['id'],
                "id": file['id'],
                "title": file['title']
            })

    return resources
