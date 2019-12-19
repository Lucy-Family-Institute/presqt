import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def zenodo_download_helper(is_record, base_url, auth_parameter, files, file_url=None):
    """
    This is used in Zenodo's download function.

    Parameters
    ----------
    is_record : boolean
        Flag for if the download is a public record
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

    if is_record is True:
        # Record endpoints are inconsistent, so there are a few checks that need to happen.
        try:
            username = project_helper['owners'][0]
        except KeyError:
            username = None
        try:
            project_name = project_helper['metadata']['title']
        except KeyError:
            project_name = None
    else:
        # The deposition endpoints are consistent
        username = project_helper['owner']
        project_name = project_helper['title']

    action_metadata = {"sourceUsername": username}

    if file_url:
        metadata_helper = requests.get(file_url, params=auth_parameter).json()
        files = zenodo_file_download_helper(
            auth_parameter, is_record, project_name, metadata_helper, files)

    else:
        files = zenodo_project_download_helper(is_record, project_name, project_helper, files)

    return files, action_metadata


def zenodo_file_download_helper(auth_parameter, is_record, project_name, metadata_helper, files):
    """
    Downloads a single file from Zenodo and returns the expected dictionary.

    Parameters
    ----------
    auth_parameter : dict
        The Authentication parameter expected by Zenodo.
    is_record : bool
        Flag for if the resource is a published record
    project_name : str
        The name of the project.
    metadata_helper : dict
        JSON payload from Zenodo API
    files: list
        The list to append the file to.

    Returns
    -------
        The list of files.
    """
    if is_record is True:
        file_contents = requests.get(
            metadata_helper['contents'][0]['links']['self'], params=auth_parameter).content
        hashes = {'md5': metadata_helper['contents'][0]['checksum'].partition(':')[2]}
        title = metadata_helper['contents'][0]['key']
        path = '/{}'.format(title)
        # No way of getting project title if passed a file id.
        source_path = '/{}'.format(title)
    else:
        file_contents = requests.get(
            metadata_helper['links']['download'], params=auth_parameter).content
        hashes = {'md5': metadata_helper['checksum']}
        title = metadata_helper['filename']
        path = '/{}'.format(metadata_helper['filename'])
        source_path = "/{}/{}".format(project_name, metadata_helper['filename'])

    files.append({
        'file': file_contents,
        'hashes': hashes,
        'title': title,
        # If the file is the only resource we are downloading then we don't need it's full path.
        'path': path,
        'source_path': source_path,
        'extra_metadata': {}})

    return files


def zenodo_project_download_helper(is_record, project_name, project_helper, files):
    """
    Downloads a full project from Zenodo and returns the expected list of dictionaries.

    Parameters
    ----------
    is_record : bool
        Flag for if the resource is a published record
    project_name : str
        The name of the project.
    project_helper : dict
        JSON payload from Zenodo API
    files: list
        The list to append the file to.

    Returns
    -------
        The list of files.
    """
    if is_record is True:
        for resource in project_helper['files']:
            files.append({
                "file": resource['links']['self'],
                "hashes": {'md5': resource['checksum'].partition(':')[2]},
                "title": resource['key'],
                "path": "/{}/{}".format(project_name, resource['key']),
                "source_path": "/{}/{}".format(project_name, resource['key']),
                "extra_metadata": {}})
    else:
        for resource in project_helper['files']:
            files.append({
                "file": resource['links']['download'],
                "hashes": {'md5': resource['checksum']},
                "title": resource['filename'],
                "path": "/{}/{}".format(project_name, resource['filename']),
                "source_path": "/{}/{}".format(project_name, resource['filename']),
                "extra_metadata": {}})

    return files
