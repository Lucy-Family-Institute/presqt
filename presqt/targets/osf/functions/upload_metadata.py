import itertools
import json
import requests

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.targets.osf.classes.main import OSF
from presqt.targets.osf.utilities import get_osf_resource
from presqt.utilities import PresQTError


def osf_upload_metadata(token, project_id, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the repo.

    Parameters
    ----------
    token : str
        The user's OSF token
    project_id : str
        An id the upload is taking place on
    metadata_dict : dict
        The metadata to be written to the project
    """
    osf_instance = OSF(token)
    header = {'Authorization': 'Bearer {}'.format(token)}
    file_name = 'PRESQT_FTS_METADATA.json'
    encoded_metadata = json.dumps(metadata_dict, indent=4).encode('utf-8')
    put_url = "https://files.osf.io/v1/resources/{}/providers/osfstorage/"

    # We need to find out if this project already has metadata associated with it.
    project_data = osf_instance._get_all_paginated_data(
        'https://api.osf.io/v2/nodes/{}/files/osfstorage'.format(project_id))

    for data in project_data:
        if data['attributes']['name'] == file_name:
            old_metadata_file = requests.get(data['links']['move'], headers=header).content
            # Update the existing metadata
            updated_metadata = json.loads(old_metadata_file)

            if schema_validator('presqt/json_schemas/metadata_schema.json', updated_metadata) is not True:
                # We need to change the file name, this metadata is improperly formatted and
                # therefore invalid.
                rename_payload = {"action": "rename",
                                  "rename": "INVALID_PRESQT_FTS_METADATA.json"}
                response = requests.post(data['links']['move'], headers=header,
                                         data=json.dumps(rename_payload).encode('utf-8'))
                if response.status_code != 201:
                    raise PresQTError(
                        "The request to rename the invalid metadata file has returned a {} error code from OSF.".format(
                            response.status_code))
                break

            # Loop through each 'action' in both metadata files and make a new list of them.
            joined_actions = [entry for entry in itertools.chain(metadata_dict['actions'],
                                                                 updated_metadata['actions'])]

            updated_metadata['actions'] = joined_actions
            encoded_metadata = json.dumps(updated_metadata, indent=4).encode('utf-8')

            # Now we need to update the metadata file with this updated metadata
            response = requests.put(data['links']['upload'], headers=header,
                                    params={'kind': 'file'}, data=encoded_metadata)
            # When updating an existing metadata file, OSF returns a 200 status
            if response.status_code != 200:
                raise PresQTError(
                    "The request to update the metadata file has returned a {} error code from OSF.".format(
                        response.status_code))
            return

    # If there is no existing metadata file, then create a new one.
    response = requests.put(put_url.format(project_id), headers=header, params={"name": file_name},
                            data=encoded_metadata)
    if response.status_code != 201:
        raise PresQTError(
            "The request to create a metadata file has resulted in a {} error code from OSF".format(
                response.status_code))
