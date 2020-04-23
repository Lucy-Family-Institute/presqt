import base64
import itertools
import json

import requests

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.targets.gitlab.utilities import validation_check
from presqt.utilities import PresQTError


def gitlab_upload_metadata(token, project_id, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the repo.

    Parameters
    ----------
    token : str
        The user's GitLab token
    project_id : str
        The id of the top level project that the upload took place on
    metadata_dict : dict
        The metadata to be written to the repo
    """
    headers, user_id = validation_check(token)

    # Check if metadata exists
    base_post_url = "https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA.json?ref=master".format(project_id)

    metadata_file_response = requests.get(base_post_url, headers=headers)
    metadata_file_data = metadata_file_response.json()

    # # If a metadata file already exists then grab its contents
    if metadata_file_response.status_code == 200:
        base64_metadata = base64.b64decode(metadata_file_data['content'])
        updated_metadata = json.loads(base64_metadata)
        if schema_validator('presqt/json_schemas/metadata_schema.json', updated_metadata) is not True:
            # We need to change the file name, this metadata is improperly formatted and
            # therefore invalid.
            invalid_base64_metadata = base64.b64encode(base64_metadata)
            data = {"branch": "master",
                    "commit_message": "PresQT Invalid Metadata Upload",
                    "encoding": "base64",
                    "content": invalid_base64_metadata}

            invalid_metadata_response = requests.post(
                'https://gitlab.com/api/v4/projects/{}/repository/files/INVALID_PRESQT_FTS_METADATA%2Ejson'.format(project_id),
                headers=headers,
                data=data)

            if invalid_metadata_response.status_code != 201:
                raise PresQTError(
                    "The request to rename the invalid metadata file has returned a {} error code from Gitlab.".format(
                        invalid_metadata_response.status_code))
        else:
            # Loop through each 'action' in both metadata files and make a new list of them.
            joined_actions = [entry for entry in itertools.chain(metadata_dict['actions'],
                                                                 updated_metadata['actions'])]

            updated_metadata['actions'] = joined_actions

            updated_metadata_bytes = json.dumps(updated_metadata, indent=4).encode('utf-8')
            updated_base64_metadata = base64.b64encode(updated_metadata_bytes)

            data = {"branch": "master",
                    "commit_message": "Updated PresQT Metadata Upload",
                    "encoding": "base64",
                    "content": updated_base64_metadata}

            metadata_response = requests.put("https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA%2Ejson".format(project_id),
                         headers=headers,
                         data=data)

            if metadata_response.status_code != 200:
                raise PresQTError(
                    "The request to update the metadata file has returned a {} error code from Gitlab.".format(
                        metadata_response.status_code))
            return


    metadata_bytes = json.dumps(metadata_dict, indent=4).encode('utf-8')
    base64_metadata = base64.b64encode(metadata_bytes)

    post_url = "https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA%2Ejson".format(project_id)

    data = {"branch": "master",
            "commit_message": "PresQT Metadata Upload",
            "encoding": "base64",
            "content": base64_metadata}

    response = requests.post(post_url, headers=headers, data=data)

    if response.status_code != 201:
        raise PresQTError(
            "The request to create a metadata file has resulted in a {} error code from GitLab.".format(
                response.status_code))