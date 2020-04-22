import base64
import itertools
import json
import requests

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.targets.github.utilities import validation_check
from presqt.utilities import PresQTError


def github_upload_metadata(token, project_id, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the repo.

    Parameters
    ----------
    token : str
        The user's GitHub token
    project_id : str
        The id of the top level project that the upload took place on
    metadata_dict : dict
        The metadata to be written to the repo
    """
    header, username = validation_check(token)

    base_put_url = "https://api.github.com/repos/{}/{}/contents/".format(username, project_id)
    metadata_file_data = requests.get('{}{}'.format(base_put_url, 'PRESQT_FTS_METADATA.json'),
                                      headers=header).json()

    try:
        sha = metadata_file_data['sha']
    except KeyError:
        sha = None

    # If a metadata file already exists then grab its contents
    if sha:
        base64_metadata = base64.b64decode(metadata_file_data['content'])
        updated_metadata = json.loads(base64_metadata)

        if schema_validator('presqt/json_schemas/metadata_schema.json', updated_metadata) is not True:
            # We need to change the file name, this metadata is improperly formatted and
            # therefore invalid.
            invalid_base64_metadata = base64.b64encode(base64_metadata).decode('utf-8')
            rename_payload = {
                "message": "PresQT Invalid Upload",
                "committer": {
                    "name": "PresQT",
                    "email": "N/A"},
                "content": invalid_base64_metadata}

            response = requests.put('{}{}'.format(base_put_url, 'INVALID_PRESQT_FTS_METADATA.json'),
                                    headers=header,
                                     data=json.dumps(rename_payload))
            if response.status_code != 201:
                raise PresQTError(
                    "The request to rename the invalid metadata file has returned a {} error code from Github.".format(
                        response.status_code))
        else:
            # Loop through each 'action' in both metadata files and make a new list of them.
            joined_actions = [entry for entry in itertools.chain(metadata_dict['actions'],
                                                                 updated_metadata['actions'])]
            updated_metadata['actions'] = joined_actions

            updated_metadata_bytes = json.dumps(updated_metadata, indent=4).encode('utf-8')
            updated_base64_metadata = base64.b64encode(updated_metadata_bytes).decode('utf-8')

            update_payload = {
                "message": "PresQT Update",
                "committer": {
                    "name": "PresQT",
                    "email": "N/A"},
                "branch": "master",
                "content": updated_base64_metadata,
                "sha": sha
            }

            # Now we need to update the metadata file with this updated metadata
            response = requests.put('{}{}'.format(base_put_url, 'PRESQT_FTS_METADATA.json'),
                                                  headers=header,
                                                  data=json.dumps(update_payload))
            if response.status_code != 200:
                raise PresQTError(
                    "The request to create a metadata file has resulted in a {} error code from GitHub.".format(
                        response.status_code))
            return

    metadata_bytes = json.dumps(metadata_dict, indent=4).encode('utf-8')
    base64_metadata = base64.b64encode(metadata_bytes).decode('utf-8')

    payload = {
        "message": "PresQT Upload",
        "sha": sha,
        "committer": {
            "name": "PresQT",
            "email": "N/A"},
        "content": base64_metadata}
    response = requests.put('{}{}'.format(base_put_url, 'PRESQT_FTS_METADATA.json'),
                                          headers=header,
                                          data=json.dumps(payload))

    if response.status_code != 201 and response.status_code != 200:
        raise PresQTError(
            "The request to create a metadata file has resulted in a {} error code from GitHub.".format(
                response.status_code))
