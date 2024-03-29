import io
import json
import os
import requests

from rest_framework import status

from presqt.api_v1.utilities.fixity.hash_generator import hash_generator
from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.targets.figshare.utilities.helpers.create_project import create_project
from presqt.targets.figshare.utilities.helpers.create_article import create_article
from presqt.targets.figshare.utilities.helpers.upload_helpers import figshare_file_upload_process
from presqt.utilities import PresQTResponseException, update_process_info, increment_process_info, update_process_info_message
from presqt.targets.utilities import get_duplicate_title, upload_total_files


def figshare_upload_resource(token, resource_id, resource_main_dir, hash_algorithm, file_duplicate_action, process_info_path, action):
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
    process_info_path: str
        Path to the process info file that keeps track of the action's progress
    action: str
        The action being performed

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
        'project_link': The link to either the resource or the home page of the user if not available through API

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
    total_files = upload_total_files(resource_main_dir)
    # Update process info file
    update_process_info(process_info_path, total_files, action, 'upload')
    update_process_info_message(process_info_path, action, "Uploading files to FigShare...")

    resources_ignored = []
    resources_updated = []
    file_metadata_list = []
    action_metadata = {'destinationUsername': username}

    # Upload a new project
    if not resource_id:
        project_title = os_path[1][0]
        # Create a new project with the name being the top level directory's name.
        project_name, project_id = create_project(project_title, headers, token)
        # Create article, for now we'll name it the same as the project
        article_id = create_article(project_title, headers, project_id)
    else:
        # Upload to an existing project
        split_id = str(resource_id).split(":")
        project_id = split_id[0]

        try:
            project_title = requests.get("https://api.figshare.com/v2/account/projects/{}".format(
                project_id), headers=headers).json()['title']
        except KeyError:
            raise PresQTResponseException(
                "Project with id, {}, could not be found by the requesting user.".format(
                    project_id), status.HTTP_400_BAD_REQUEST)

        if len(split_id) == 1:
            # We only have a project and we need to make a new article id
            # Check to see if an article with this name already exists
            articles = requests.get("https://api.figshare.com/v2/account/projects/{}/articles".format(project_id),
                                    headers=headers).json()
            article_titles = [article['title'] for article in articles]
            new_title = get_duplicate_title(project_title, article_titles, "(PresQT*)")
            article_id = create_article(new_title, headers, resource_id)
        elif len(split_id) == 2:
            article_id = split_id[1]
        else:
            # Can't upload to file
            raise PresQTResponseException(
                "Can not upload into an existing file.",
                status.HTTP_400_BAD_REQUEST)

    # Get the article title
    try:
        article_title = requests.get("https://api.figshare.com/v2/account/articles/{}".format(article_id),
                                     headers=headers).json()['title']
    except KeyError:
        raise PresQTResponseException(
            "Article with id, {}, could not be found by the requesting user.".format(
                article_id), status.HTTP_400_BAD_REQUEST)

    # Get md5, size and name of zip file to be uploaded
    for path, subdirs, files in os.walk(resource_main_dir):
        for name in files:
            file_info = open(os.path.join(path, name), 'rb')
            zip_hash = hash_generator(file_info.read(), 'md5')

            figshare_file_upload_process(file_info, headers, name, article_id, file_type='zip',
                                         path=path)

            file_metadata_list.append({
                'actionRootPath': os.path.join(path, name),
                'destinationPath': '/{}/{}/{}'.format(project_title, article_title, name),
                'title': name,
                'destinationHash': zip_hash})
            increment_process_info(process_info_path, action, 'upload')

    return {
        "resources_ignored": resources_ignored,
        "resources_updated": resources_updated,
        "action_metadata": action_metadata,
        "file_metadata_list": file_metadata_list,
        "project_id": "{}:{}".format(project_id, article_id),
        "project_link": "https://figshare.com/account/home#/projects"
    }
