import io
import json
import requests

from rest_framework import status

from presqt.api_v1.utilities.fixity.hash_generator import hash_generator
from presqt.targets.figshare.functions.upload import upload_parts
from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.utilities import PresQTResponseException


def figshare_upload_metadata(token, article_id, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the project.

    Parameters
    ----------
    token : str
        The user's FigShare token
    article_id : str
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
            "FigShare returned an error trying to upload {}. Some items may still have been created on FigShare.".format(file_name),
            status.HTTP_400_BAD_REQUEST)

    # Get location information
    file_url = upload_response.json()['location']
    get_upload_response = requests.get(file_url, headers=headers).json()
    upload_url = get_upload_response['upload_url']
    file_id = get_upload_response['id']

    # Get upload information
    file_upload_response = requests.get(upload_url, headers=headers).json()
    virtual_file = io.BytesIO(metadata_bytes)
    upload_parts(headers, upload_url, file_upload_response['parts'], virtual_file)

    complete_upload = requests.post(
        "https://api.figshare.com/v2/account/articles/{}/files/{}".format(
            article_id, file_id),
        headers=headers)

    if complete_upload.status_code != 202:
        raise PresQTResponseException(
            "FigShare returned an error trying to upload {}. Some items may still have been created on FigShare.".format(file_name),
            status.HTTP_400_BAD_REQUEST)
