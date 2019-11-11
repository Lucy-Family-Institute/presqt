import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def zenodo_download_helper(base_url, auth_parameter, files, file_url=None):
    """
    This is used in Zenodo's download function.

    Parameters
    ----------
    base_url : str
        The url of the Zenodo project.
    auth_parameter : str
        The Authentication parameter expected by Zenodo.
    files : list
        The list of files to append to.
    file_url : str
        If the download is a single file, we also pass the link to the file.

    Returns
    -------
    The list of file dictionaries and action_metadata.
    """
    project_info = requests.get(base_url, auth_parameter)

    if project_info.status_code != 200:
        raise PresQTResponseException('The response returned a 404 not found status code.',
                                      status.HTTP_404_NOT_FOUND)

    project_helper = project_info.json()
    username = project_helper['owner']
    project_name = project_helper['title']

    action_metadata = {"sourceUsername": username}

    if file_url:
        metadata_helper = requests.get(file_url, params=auth_parameter).json()

        file_contents = requests.get(
            metadata_helper['links']['download'], params=auth_parameter).content

        files.append({
            'file': file_contents,
            'hashes': {'md5': metadata_helper['checksum']},
            'title': metadata_helper['filename'],
            # If the file is the only resource we are downloading then we don't need it's full path.
            'path': '/{}'.format(metadata_helper['filename']),
            'source_path': "/{}/{}".format(project_name, metadata_helper['filename']),
            'extra_metadata': {}})

    else:
        for resource in project_helper['files']:
            files.append({
                "file": resource['links']['download'],
                "hashes": {'md5': resource['checksum']},
                "title": resource['filename'],
                "path": "/{}/{}".format(project_name, resource['filename']),
                "source_path": "/{}/{}".format(project_name, resource['filename']),
                "extra_metadata": {}})

    return files, action_metadata
