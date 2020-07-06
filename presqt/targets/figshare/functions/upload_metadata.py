import itertools
import json
import requests

from rest_framework import status

from presqt.api_v1.utilities.fixity.hash_generator import hash_generator
from presqt.json_schemas.schema_handlers import schema_validator
from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.utilities import PresQTError, PresQTResponseException


def figshare_upload_metadata(token, article_id, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the project.

    Parameters
    ----------
    token : str
        The user's FigShare token
    project_id : str
        The id of the article that the upload took place on
    metadata_dict : dict
        The metadata to be written to the repo
    """
    try:
        headers, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    file_name = 'PRESQT_FTS_METADATA.json'
    file_url = "https://api.figshare.com/v2/account/articles/{}/files".format(article_id)

    project_files = requests.get(file_url, headers=headers).json()

    for file in project_files:
        if file['name'] == file_name:
            # Do stuff here
            pass

    metadata_bytes = json.dumps(metadata_dict, indent=4).encode('utf-8')
    metadata_size = len(metadata_bytes)
    metadata_hash = hash_generator(metadata_bytes, 'md5')

    file_data = {
        "md5": metadata_hash,
        "name": file_name,
        "size": metadata_size
    }

    upload_response = requests.post(file_url, headers=headers, data=json.dumps(file_data))

    if upload_response.status_code != 201:
        raise PresQTResponseException(
            "FigShare returned an error trying to upload {}.".format(file_name),
            status.HTTP_400_BAD_REQUEST)

    # Get location information
    file_url = upload_response.json()['location']
    upload_response = requests.get(file_url, headers=headers).json()
    upload_url = upload_response['upload_url']
    file_id = upload_response['id']

    # Get upload information
    file_upload_response = requests.get(upload_url, headers=headers).json()

    headers["Content-Type"] = "application/binary"
    for part in file_upload_response['parts']:
        upload_status = requests.put(
            "{}/{}".format(upload_url, part['partNo']), headers=headers, data=metadata_bytes)
        if upload_status.status_code != 200:
            raise PresQTResponseException(
                "FigShare returned an error trying to upload.", status.HTTP_400_BAD_REQUEST)

    complete_upload = requests.post(
        "https://api.figshare.com/v2/account/articles/{}/files/{}".format(
            article_id, file_id),
        headers=headers)
