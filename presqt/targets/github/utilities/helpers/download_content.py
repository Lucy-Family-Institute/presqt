import base64

import requests

from presqt.utilities import increment_process_info, update_process_info


def download_content(username, url, header, repo_name, files, process_info_path):
    """
    Recursive function to extract all files from a given repo.

    Parameters
    ----------
    username : str
        The user's GitHub username.
    url : str
        The url of the repo's contents
    header: dict
        API header expected by GitHub
    repo_name : str
        The name of the repo that is being downloaded
    files : list
        A list of dictionaries with file information
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    A list of file dictionaries and a list of empty containers
    """
    initial_data = requests.get(url, headers=header).json()
    action_metadata = {"sourceUsername": username}
    # Loop through the initial data and build up the file urls and if the type is directory
    # recursively call function.
    for data in initial_data:
        if data['type'] == 'file':
            file_metadata = {"commit_hash": data['sha']}
            for key, value in data.items():
                if key not in ['name', 'path', 'sha']:
                    file_metadata[key] = value

            files.append({
                'file': data['download_url'],
                'hashes': {},
                'title': data['name'],
                'path': '/{}/{}'.format(repo_name, data['path']),
                'source_path': '/{}/{}'.format(repo_name, data['path']),
                'extra_metadata': file_metadata})
            # Increment the number of files done in the process info file.
            increment_process_info(process_info_path, 'resource_download')
        else:
            download_content(username, data['url'], header, repo_name, files, process_info_path)

    return files, [], action_metadata

def download_directory(header, path_to_resource, repo_data, process_info_path):
    """
    Go through a repo's tree and download all files inside of a given resource directory path.

    Parameters
    ----------
    header: dict
        API header expected by GitHub
    path_to_resource: str
        The path to the requested directory
    repo_data: dict
        Repository data gathered in the repo GET request
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    A list of dictionaries for each file being downloaded
    """
    repo_name = repo_data['name']
    # Strip {/sha} off the end
    trees_url = '{}/master?recursive=1'.format(repo_data['trees_url'][:-6])
    contents = requests.get(trees_url, headers=header).json()

    number_of_files = len([file for file in contents['tree'] if file['path'].startswith(path_to_resource) and file['type'] == 'blob'])
    # Add the total number of repository to the process info file.
    # This is necessary to keep track of the progress of the request.
    update_process_info(process_info_path, number_of_files, 'resource_download')

    files = []
    for resource in contents['tree']:
        if resource['path'].startswith(path_to_resource) and resource['type'] == 'blob':
            # Strip the requested directory's parents off the directory path
            path_to_strip = path_to_resource.rpartition('/')[0]
            if path_to_strip:
                directory_path = '{}'.format(resource['path'].partition(path_to_strip)[2])
            else:
                directory_path = '/{}'.format(resource['path'])

            file_data = requests.get(resource['url']).json()

            files.append({
                'file': base64.b64decode(file_data['content']),
                'hashes': {},
                'title': resource['path'].rpartition('/')[0],
                'path': directory_path,
                'source_path': '/{}/{}'.format(repo_name, resource['path']),
                'extra_metadata': {}
            })
            # Increment the number of files done in the process info file.
            increment_process_info(process_info_path, 'resource_download')
    return files

def download_file(repo_data, resource_data, process_info_path):
    """
    Build a dictionary for the requested file

    Parameters
    ----------
    repo_data: dict
        Repository data gathered in the repo GET request
    resource_data:
        Resource data gathered in the resource GET request
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    A list of a single dictionary representing the file requested and delivered. Boom.
    """
    repo_name = repo_data['name']
    # Increment the number of files done in the process info file.
    increment_process_info(process_info_path, 'resource_download')
    return [{
        'file': base64.b64decode(resource_data['content']),
        'hashes': {},
        'title': resource_data['name'],
        'path': '/{}'.format(resource_data['name']),
        'source_path': '/{}/{}'.format(repo_name, resource_data['path']),
        'extra_metadata': {}
    }]