import itertools
import json
import requests

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.targets.zenodo.utilities import zenodo_validation_check
from presqt.utilities import PresQTError


def zenodo_upload_metadata(token, project_id, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the project.

    Parameters
    ----------
    token : str
        The user's Zenodo token
    project_id : str
        The id of the top level project that the upload took place on
    metadata_dict : dict
        The metadata to be written to the repo
    """
    auth_parameter = zenodo_validation_check(token)
    post_url = "https://zenodo.org/api/deposit/depositions/{}/files".format(project_id)
    file_name = 'PRESQT_FTS_METADATA.json'

    project_files = requests.get(post_url, params=auth_parameter).json()

    for file in project_files:
        if file['filename'] == file_name:
            # Download the metadata
            old_metadata_file = requests.get(file['links']['download'],
                                             params=auth_parameter).content
            # Load the existing metadata to be updated.
            updated_metadata = json.loads(old_metadata_file)

            if schema_validator('presqt/json_schemas/metadata_schema.json', updated_metadata) is not True:
                # We need to change the file name, this metadata is improperly formatted and
                # therefore invalid. Zenodo is having issues with their put method atm.......
                # Need to delete the old metadata file.
                requests.delete(file['links']['self'], params=auth_parameter)
                response_status = metadata_post_request('INVALID_PRESQT_FTS_METADATA.json',
                                                        updated_metadata, auth_parameter, post_url)
                if response_status != 201:
                    raise PresQTError(
                        "The request to rename the invalid metadata file has returned a {} error code from Zenodo.".format(
                            response_status))
                break

            # Need to delete the old metadata file.
            requests.delete(file['links']['self'], params=auth_parameter)

            # Loop through each 'action' in both metadata files and make a new list of them.
            joined_actions = [entry for entry in itertools.chain(metadata_dict['actions'],
                                                                 updated_metadata['actions'])]
            joined_keywords = [entry for entry in itertools.chain(metadata_dict['allKeywords'],
                                                                  updated_metadata['allKeywords'])]
            updated_metadata['actions'] = joined_actions
            updated_metadata['allKeywords'] = list(set(joined_keywords))

            response_status = metadata_post_request(file_name, updated_metadata, auth_parameter,
                                                    post_url)
            # When updating an existing metadata file, Zenodo returns a 201 status
            if response_status != 201:
                raise PresQTError(
                    "The request to update the metadata file has returned a {} error code from Zenodo.".format(
                        response_status))
            return

    response_status = metadata_post_request(file_name, metadata_dict, auth_parameter, post_url)
    if response_status != 201:
        raise PresQTError(
            "The request to create a metadata file has resulted in a {} error code from Zenodo.".format(
                response_status))


def metadata_post_request(file_name, metadata, auth_parameter, url):
    """
    Used to structure and make the post request for metadata to Zenodo.

    Parameters
    ----------
    file_name : str
        The name of the file to be created.
    metadata : dict
        The PresQT metadata file to be created.
    auth_parameter : dict
        The Zenodo authentication parameter.
    url : str
        The url to issue the post request.

    Returns
    -------
    The status code of the request.
    """
    # Prepare the request values
    data = {'name': file_name}
    metadata_bytes = json.dumps(metadata, indent=4).encode('utf-8')
    files = {'file': metadata_bytes}

    # Make the request
    response = requests.post(url, params=auth_parameter, data=data, files=files)

    return response.status_code
