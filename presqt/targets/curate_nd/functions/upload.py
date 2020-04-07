import json
import os
import requests

from rest_framework import status

from presqt.targets.curate_nd.classes.main import CurateND
from presqt.utilities import (PresQTResponseException,
                              PresQTValidationError,
                              PresQTInvalidTokenError)


def curate_nd_upload_resource(token, resource_id, resource_main_dir, hash_algorithm, file_duplicate_action):
    """
    Upload the files found in the resource_main_dir to CurateND.

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
    """
    try:
        CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTValidationError("Token is invalid. Response returned a 401 status code.",
                                    status.HTTP_401_UNAUTHORIZED)

    header = {'X-Api-Token': token}

    os_path = next(os.walk(resource_main_dir))

    if resource_id:
        raise PresQTResponseException(
            "Can't upload to an existing CurateND item.", status.HTTP_400_BAD_REQUEST)
    else:
        # Change this...
        action_metadata = {"destinationUsername": "PUT IT HERE"}
        project_title = os_path[1][0]
        # PUT TITLE HELPER STUFF HERE
        trx_id = requests.get('https://curatepprd.library.nd.edu/api/uploads/new',
                              headers=header, data=json.dumps({'title': project_title})).json()['trx_id']

        # Add Content-Type to headers
        header['Content-Type'] = 'application/x-www-form-urlencoded'

        resources_ignored = []
        file_metadata_list = []
        resources_updated = []

        for path, subdirs, files in os.walk(resource_main_dir):
            if not subdirs and not files:
                resources_ignored.append(path)
            for name in files:
                print(name)
                bfile = open(os.path.join(path, name), 'rb')
                print(bfile)
                post_url = 'https://curatepprd.library.nd.edu/api/uploads/{}/file/new?file_name={}'.format(
                    trx_id, name)
                response = requests.post(post_url, headers=header, data=bfile)
                print('FILE POST')
                print(response.status_code)
                print(response.json())
                print('\n')

                if response.status_code != 200:
                    raise PresQTResponseException(
                        "CurateND returned an error trying to upload {}".format(name),
                        status.HTTP_400_BAD_REQUEST)

                file_metadata_list.append({
                    'actionRootPath': os.path.join(path, name),
                    'destinationPath': '/{}/{}'.format(project_title, name),
                    'title': name,
                    'destinationHash': None})

    # Because of the way CurateNDs API is handling upload, we have to make the final commit in
    # the upload_metadata function.

    return {
        "resources_ignored": resources_ignored,
        "resources_updated": resources_updated,
        "action_metadata": action_metadata,
        "file_metadata_list": file_metadata_list,
        "project_id": trx_id,
    }
