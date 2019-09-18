import requests


def download_content(url, header, repo_name, files):
    """
    Recursive function to extract all files from a given repo.

    Parameters
    ----------
    url : str
        The url of the repo's contents
    header: dict
        API header expected by GitHub
    repo_name : str
        The name of the repo that is being downloaded
    files : list
        A list of dictionaries with file information

    Returns
    -------
    A list of files and a list of empty containers
    """
    inital_data = requests.get(url, headers=header).json()
    # Loop through the inital data and build up file content and if the type is directory
    # recursively call function.
    for data in inital_data:
        if data['type'] == 'file':
            files.append({
                'file': requests.get(data['download_url'], headers=header).content,
                'hashes': {'sha1': data['sha']},
                'title': data['name'],
                'path': '/{}/{}'.format(repo_name, data['path'])})
        else:
            download_content(data['url'], header, repo_name, files)

    return files, []
