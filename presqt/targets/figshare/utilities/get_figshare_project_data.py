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
        article_get = requests.get("https://api.figshare.com/v2/account/projects/{}/articles".format(
            project['id']), headers=headers).json()

        for article in article_get:
            resources.append({
                "kind": "container",
                "kind_name": article["defined_type_name"],
                "container": project['id'],
                "id": "{}:{}".format(project['id'], article['id']),
                "title": article['title']
            })
            file_get = requests.get(article['url'], headers=headers).json()

            for file in file_get['files']:
                resources.append({
                    "kind": "item",
                    "kind_name": "file",
                    "container": "{}:{}".format(project['id'], article['id']),
                    "id": "{}:{}:{}".format(project['id'], article['id'], file['id']),
                    "title": file['name']
                })

    return resources


def get_search_project_data(initial_data, headers, resources):
    """
    Get all directories and files of a given project.

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
    resources.append({
        "kind": "container",
        "kind_name": "project",
        "container": None,
        "id": initial_data['id'],
        "title": initial_data['title']
    })

    article_get = requests.get("https://api.figshare.com/v2/projects/{}/articles".format(
        initial_data['id']), headers=headers).json()

    for article in article_get:
        resources.append({
            "kind": "container",
            "kind_name": article['defined_type_name'],
            "container": initial_data['id'],
            "id": "{}:{}".format(initial_data['id'], article['id']),
            "title": article['title']
        })
        file_get = requests.get(article['url'], headers=headers).json()

        for file in file_get['files']:
            resources.append({
                "kind": "item",
                "kind_name": "file",
                "container": "{}:{}".format(initial_data['id'], article['id']),
                "id": "{}:{}:{}".format(initial_data['id'], article['id'], file['id']),
                "title": file['name']
            })

    return resources
