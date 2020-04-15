import urllib.parse


def get_gitlab_project_data(initial_data, headers, resources=[]):
    """
    """
    from presqt.targets.gitlab.utilities.gitlab_paginated_data import gitlab_paginated_data

    for project in initial_data:
        if ('marked_for_deletion_at' in project.keys() and not project['marked_for_deletion_at']) or (
                'marked_for_deletion_at' not in project.keys()):
            tree_url = '{}/{}'.format(project['_links']['self'], 'repository/tree?recursive=1')
            file_data = gitlab_paginated_data(headers, None, tree_url)
            print(file_data)

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
