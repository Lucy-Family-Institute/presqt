import requests


def download_content(username, project_name, resource_id, data, files, is_project):
    """
    Recursive function to extract all files from a given project.

    Parameters
    ----------
    username: str
        The user's Gitlab username
    project_name: str
        The name of the project being downloaded
    resource_id: str
        The id of the resource being downloaded
    data: dict
        The initial project data
    files : list
        A list of dictionaries with file information
    is_project: boolean
        Whether what is to be downloaded is a project or not

    Returns
    -------
    A list of file dictionaries and a list of empty containers
    """
    action_metadata = {"sourceUsername": username}

    # Loop through all data and create links where the file contents can be retrieved from
    for entry in data:
        if entry['type'] == 'blob':
            entry_path = entry['path'].replace('/', '%2F')
            file_url = "https://gitlab.com/api/v4/projects/{}/repository/files/{}?ref=master".format(
                resource_id, entry_path)
            # Format the path given a project or a directory
            if is_project:
                file_path = "/{}/{}".format(project_name, entry['path'])
            else:
                file_path = "/{}".format(entry['path'])

            files.append({
                'file': file_url,
                'hashes': {},
                'title': entry['name'],
                'path': file_path,
                'source_path': "/{}/{}".format(project_name, entry['path']),
                'extra_metadata': {}})

    return files, [], action_metadata
