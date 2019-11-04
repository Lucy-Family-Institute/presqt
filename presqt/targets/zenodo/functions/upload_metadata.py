import itertools
import json
import requests

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.targets.zenodo.utilities import zenodo_validation_check
from presqt.utilities import PresQTError


def zenodo_upload_metadata(token, resource_id, metadata_dict, project_id):
    """
    Upload the metadata of this PresQT action at the top level of the project.

    Parameters
    ----------
    token : str
        The user's Zenodo token
    resource_id : str
        An id the upload is taking place on (not used for Zenodo)
    metadata_dict : dict
        The metadata to be written to the repo
    project_id : str
        The id of the project that has been created
    """
    auth_parameter = zenodo_validation_check(token)
    post_url = "https://zenodo.org/api/deposit/depositions/{}/files".format(project_id)
    file_name = 'PRESQT_FTS_METADATA.json'

    find_old_metadata = requests.get(post_url, params=auth_parameter).json()

    for file in find_old_metadata:
        if file['filename'] == file_name:
            # Download the metadata
            old_metadata_file = requests.get(file['links']['download'],
                                             params=auth_parameter).content
            # Update the existing metadata
            updated_metadata = json.loads(old_metadata_file)
            print(updated_metadata)

            if schema_validator('presqt/json_schemas/metadata_schema.json', updated_metadata) is not True:
                print("WHAT")
                print(schema_validator('presqt/json_schemas/metadata_schema.json', updated_metadata))
                # We need to change the file name, this metadata is improperly formatted and
                # therefore invalid.
                rename_payload = {"name": "INVALID_PRESQT_FTS_METADATA.json"}
                headers = {"Content-Type": "application/json"}
                response = requests.post(file['links']['self'], headers=headers,
                                         params=auth_parameter, data=json.dumps(rename_payload))
                if response.status_code != 201:
                    raise PresQTError(
                        "The request to rename the invalid metadata file has returned a {} error code from OSF.".format(
                            response.status_code))
                break

            # Need to delete the old metadata file.....thanks Zenodo.
            egg = requests.delete(file['links']['self'], params=auth_parameter)
            print(egg.status_code)
            # Loop through each 'action' in both metadata files and make a new list of them.
            joined_actions = [entry for entry in itertools.chain(metadata_dict['actions'],
                                                                 updated_metadata['actions'])]
            updated_metadata['actions'] = joined_actions
            metadata_bytes = json.dumps(updated_metadata, indent=4).encode('utf-8')
            files = {'file': metadata_bytes}
            # Now we need to update the metadata file with this updated metadata
            data = {'name': file_name}
            response = requests.put(post_url, params=auth_parameter,
                                    data=data, files=files)
            # When updating an existing metadata file, OSF returns a 200 status
            if response.status_code != 200:
                raise PresQTError(
                    "The request to update the metadata file has returned a {} error code from OSF.".format(
                        response.status_code))
            return

    data = {'name': file_name}
    metadata_bytes = json.dumps(metadata_dict, indent=4).encode('utf-8')

    files = {'file': metadata_bytes}

    response = requests.post(post_url, params=auth_parameter, data=data, files=files)

    if response.status_code != 201:
        raise PresQTError(
            "The request to create a metadata file has resulted in a {} error code from Zenodo.".format(
                response.status_code))
