import urllib.parse
import requests

from presqt.utilities import update_process_info, increment_process_info


def get_github_repository_data(initial_data, header, process_info_path, resources=[]):
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
    process_info_path: str
        Path to the process info file that keeps track of the action's progress


    Returns
    -------
    The user's resources.
    """

    # Add the total number of repository to the process info file.
    # This is necessary to keep track of the progress of the request.
    update_process_info(process_info_path, len(initial_data), 'resource_collection', 'fetch')

    for repo in initial_data:
        resources.append({
            "kind": "container",
            "kind_name": "repo",
            "container": None,
            "id": repo["id"],
            "title": repo["name"]})

        # Strip {/sha} off the end
        # trees_url = '{}/master?recursive=1'.format(repo['trees_url'][:-6])
        # contents = requests.get(trees_url, headers=header).json()

        # if 'message' not in contents.keys():
        #     for resource in contents['tree']:
        #         formatted_id = '{}:{}'.format(
        #             repo["id"], urllib.parse.quote_plus(resource['path']).replace(".", "%252E"))
        #         title = resource['path'].rpartition('/')[2]

        #         if title == resource['path']:
        #             container = repo["id"]
        #         else:
        #             container = '{}:{}'.format(
        #                 repo["id"], urllib.parse.quote_plus(resource['path'].rpartition('/')[0]))

        #         if resource['type'] == 'blob':
        #             resources.append({
        #                 "kind": "item",
        #                 "kind_name": "file",
        #                 "container": container,
        #                 "id": formatted_id,
        #                 "title": title
        #             })
        #         elif resource['type'] == 'tree':
        #             resources.append({
        #                 "kind": "container",
        #                 "kind_name": "folder",
        #                 "container": container,
        #                 "id": formatted_id,
        #                 "title": title
        #             })
        # Increment the number of files done in the process info file.
        increment_process_info(process_info_path, 'resource_collection', 'fetch')

    return resources
