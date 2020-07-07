import base64
import json
import os
import requests

from rest_framework import status

from presqt.api_v1.utilities.fixity.hash_generator import hash_generator
from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.targets.figshare.utilities.helpers.create_project import create_project
from presqt.targets.figshare.utilities.helpers.create_article import create_article
from presqt.utilities import PresQTResponseException, write_file, read_file


def figshare_upload_resource(token, resource_id, resource_main_dir, hash_algorithm, file_duplicate_action):
    """
    Upload the files found in the resource_main_dir to the target.

    Parameters
    ----------
    token : str
        User's token.
    resource_id : str
        ID of the resource requested.
    resource_main_dir : str
        Path to the main directory for the resources to be uploaded.
    hash_algorithm : str
        Hash algorithm we are using to check for fixity.
    file_duplicate_action : str
        The action to take when a duplicate file is found

    Returns
    -------
    Dictionary with the following keys: values
        'resources_ignored' : Array of string file paths of files that were ignored when
        uploading the resource. Path should have the same base as resource_main_dir.
                                Example:
                                    ['path/to/ignored/file.pg', 'another/ignored/file.jpg']

        'resources_updated' : Array of string file paths of files that were updated when
         uploading the resource. Path should have the same base as resource_main_dir.
                                 Example:
                                    ['path/to/updated/file.jpg']
        'action_metadata': Dictionary containing action metadata. Must be in the following format:
                            {
                                'destinationUsername': 'some_username'
                            }
        'file_metadata_list': List of dictionaries for each file that contains metadata
                              and hash info. Must be in the following format:
                                {
                                    "actionRootPath": '/path/on/disk',
                                    "destinationPath": '/path/on/target/destination',
                                    "title": 'file_title',
                                    "destinationHash": {'hash_algorithm': 'the_hash'}}
                                }
        'project_id': ID of the parent project for this upload. Needed for metadata upload.

    FigShare's Upload Process
        1. Initiate new file upload (POST) within the article. Send file size, md5, and name but no file contents yet.
        2. Send a GET request to the 'Uploader Service' to determine that the status is "Pending" and how many parts to split the upload into.
        3. Split the file into the correct number of parts and upload each using a PUT request.
        4. Send a POST request to complete the upload.
    """
    try:
        headers, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    os_path = next(os.walk(resource_main_dir))
    resources_ignored = []
    resources_updated = []
    file_metadata_list = []
    action_metadata = {'destinationUsername': username}

    project_title = os_path[1][0]

    # Upload a new project
    if not resource_id:
        # Create a new project with the name being the top level directory's name.
        project_name, project_id = create_project(project_title, headers, token)

        # Create article, for now we'll name it the same as the project
        article_id = create_article(project_title, headers, project_id)
    else:
        # Upload to an existing project
        split_id = str(resource_id).split(":")
        project_id = split_id[0]
        if len(split_id) == 1:
            # We only have a project and we need to make a new article id
            article_id = create_article(project_title, headers, resource_id)
        elif len(split_id) == 2:
            article_id = split_id[1]
        else:
            # Can't upload to file
            raise PresQTResponseException(
                "Can not upload into an existing file.",
                status.HTTP_400_BAD_REQUEST)

    # Get the article title
    article_title = requests.get("https://api.figshare.com/v2/account/articles/{}".format(article_id),
                                 headers=headers).json()['title']

    # Get md5, size and name of zip file to be uploaded
    for path, subdirs, files in os.walk(resource_main_dir):
        if not subdirs and not files:
            resources_ignored.append(path)
        for name in files:
            file_info = open(os.path.join(path, name), 'rb')
            zip_hash = hash_generator(file_info.read(), 'md5')
            zip_size = os.path.getsize(os.path.join(path, name))

            file_data = {
                "md5": zip_hash,
                "name": name,
                "size": zip_size
            }

            file_metadata_list.append({
                'actionRootPath': os.path.join(path, name),
                'destinationPath': '/{}/{}/{}'.format(project_title, article_title, name),
                'title': name,
                'destinationHash': zip_hash})

            # Initiate file upload
            upload_response = requests.post(
                "https://api.figshare.com/v2/account/articles/{}/files".format(article_id),
                headers=headers,
                data=json.dumps(file_data))

            if upload_response.status_code != 201:
                raise PresQTResponseException(
                    "FigShare returned an error trying to upload {}. Some items may still have been created on FigShare.".format(
                        name),
                    status.HTTP_400_BAD_REQUEST)

            # Get location information
            file_url = upload_response.json()['location']
            upload_response = requests.get(file_url, headers=headers).json()
            upload_url = upload_response['upload_url']
            file_id = upload_response['id']

            # Get upload information
            file_upload_response = requests.get(upload_url, headers=headers).json()
            # Loop through parts and upload
            upload_parts(headers, upload_url, file_upload_response['parts'], file_info)

            # If all complete
            complete_upload = requests.post(
                "https://api.figshare.com/v2/account/articles/{}/files/{}".format(
                    article_id, file_id),
                headers=headers)

            if complete_upload.status_code != 202:
                raise PresQTResponseException(
                    "FigShare returned an error trying to upload {}. Some items may still have been created on FigShare.".format(
                        name),
                    status.HTTP_400_BAD_REQUEST)

    return {
        "resources_ignored": resources_ignored,
        "resources_updated": resources_updated,
        "action_metadata": action_metadata,
        "file_metadata_list": file_metadata_list,
        "project_id": "{}:{}".format(project_id, article_id)
    }


def upload_parts(headers, upload_url, parts, file_info):
    """
    Upload the parts of the file to FigShare. File offsets are determined by the initial
    FigShare POST upload.
    """
    headers["Content-Type"] = "application/binary"
    for part in parts:
        file_info.seek(part['startOffset'])
        data = file_info.read(part['endOffset'] - part['startOffset'] + 1)
        upload_status = requests.put(
            "{}/{}".format(upload_url, part['partNo']), headers=headers, data=data)
        if upload_status.status_code != 200:
            raise PresQTResponseException(
                "FigShare returned an error trying to upload. Some items may still have been created on FigShare.", status.HTTP_400_BAD_REQUEST)
