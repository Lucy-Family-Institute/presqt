import urllib.parse


def get_gitlab_project_data(initial_data, headers, resources):
    """
    Get all directories and files of given projects.

    Parameters
    ----------
    initial_data: list
        List of all top level projects
    headers: dict
        The authorizaion header that GitLab expects
    resources: list
        A lis of resources to append to

    Returns
    -------
    A list of resources.

    """
    from presqt.targets.gitlab.utilities.gitlab_paginated_data import gitlab_paginated_data

    for project in initial_data:
        if ('marked_for_deletion_at' in project.keys() and not project['marked_for_deletion_at']) or (
                'marked_for_deletion_at' not in project.keys()):
            tree_url = 'https://gitlab.com/api/v4/projects/{}/repository/tree?recursive=1'.format(
                project['id'])

            file_data = gitlab_paginated_data(headers, None, tree_url)

            resources.append({
                "kind": "container",
                "kind_name": "project",
                "container": None,
                "id": project['id'],
                "title": project['name']})

            for entry in file_data:
                if '/' in entry['path']:
                    container_id = "{}:{}".format(project['id'], urllib.parse.quote_plus(entry[
                        'path'].rpartition('/')[0].replace(".", "%2E")))
                else:
                    container_id = project['id']
                type_id = "{}:{}".format(project['id'], urllib.parse.quote_plus(entry[
                    'path']).replace(".", "%2E"))
                if entry['type'] == 'blob':
                    resource = {
                        "kind": "item",
                        "kind_name": "file",
                        "container": container_id,
                        "id": type_id,
                        "title": entry['name']}
                    resources.append(resource)

                elif entry['type'] == 'tree':
                    resource = {
                        "kind": "container",
                        "kind_name": "dir",
                        "container": container_id,
                        "id": type_id,
                        "title": entry['name']}
                    resources.append(resource)

    return resources
