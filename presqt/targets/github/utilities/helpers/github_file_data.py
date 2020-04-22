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
        The user's resources.

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

        # Strip {/sha} off the end
        trees_url = '{}/master?recursive=1'.format(repo['trees_url'][:-6])
        contents = requests.get(trees_url, headers=header).json()

        if 'message' not in contents.keys():
            for resource in contents['tree']:
                formatted_id = '{}:{}'.format(
                    repo["id"], urllib.parse.quote_plus(resource['path']).replace(".", "%252E"))
                title = resource['path'].rpartition('/')[2]

                if title == resource['path']:
                    container = repo["id"]
                else:
                    container = '{}:{}'.format(
                        repo["id"], urllib.parse.quote_plus(resource['path'].rpartition('/')[0]))

                if resource['type'] == 'blob':
                    resources.append({
                        "kind": "item",
                        "kind_name": "file",
                        "container": container,
                        "id": formatted_id,
                        "title": title
                    })
                elif resource['type'] == 'tree':
                    resources.append({
                        "kind": "container",
                        "kind_name": "folder",
                        "container": container,
                        "id": formatted_id,
                        "title": title
                    })
    return resources
