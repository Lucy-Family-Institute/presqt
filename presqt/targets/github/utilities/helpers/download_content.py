import requests


def download_content(repo_info_dict, url, header, repo_name, files):
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
    A list of file dictionaries and a list of empty containers
    """
    initial_data = requests.get(url, headers=header).json()
    action_metadata = {"sourceUsername": repo_info_dict['username']}
    # Loop through the inital data and build up the file urls and if the type is directory
    # recursively call function.
    for data in initial_data:
        if data['type'] == 'file':
            file_metadata = {
                "sourcePath": repo_info_dict['repo_name'] + '/' + data['path'],
                "title": data['name'],
                "sourceHashes": None,
                "extra": {
                    "commit_hash": data['sha']}}
            for key, value in data.items():
                if key not in ['name', 'path', 'sha']:
                    file_metadata['extra'][key] = value

            files.append({
                'file': data['download_url'],
                'hashes': {},
                'title': data['name'],
                'path': '/{}/{}'.format(repo_name, data['path']),
                'metadata': file_metadata})
            print(file_metadata)
        else:
            download_content(repo_info_dict, data['url'], header, repo_name, files)

    return files, [], action_metadata
