import requests
import io
import json
import os

from rest_framework import status

from presqt.api_v1.utilities.fixity.hash_generator import hash_generator
from presqt.utilities import PresQTResponseException


def upload_parts(headers, upload_url, parts, file):
    """
    Upload the parts of the file to FigShare. File offsets are determined by the initial
    FigShare POST upload.

    Parameters
    ----------
    headers: dict
      The user's FigShare Auth headers
    upload_url: str
        The url to upload the file
    parts: list
        List of parts to be uploaded
    file: bytes
        The file itself
    """
    headers["Content-Type"] = "application/binary"
    for part in parts:
        file.seek(part['startOffset'])
        data = file.read(part['endOffset'] - part['startOffset'] + 1)
        upload_status = requests.put(
            "{}/{}".format(upload_url, part['partNo']), headers=headers, data=data)
        if upload_status.status_code != 200:
            raise PresQTResponseException(
                "FigShare returned an error trying to upload. Some items may still have been created on FigShare.", status.HTTP_400_BAD_REQUEST)


def figshare_file_upload_process(file, headers, file_name, article_id, file_type='json', path=None):
    """
    This function covers the file upload process for FigShare.

    Parameters
    ----------
    file: bytes or dict
        The file to be uploaded
    headers: dict
        The user's FigShare Auth header
    file_name: str
        The name of the file being uploaded
    article_id: str
        The id of the article to upload to
    file_type: str
        Type of file to be formatted
    path: str
        The path to the file
    """
    if file_type == 'json':
        metadata_bytes = json.dumps(file, indent=4).encode('utf-8')
        virtual_file = io.BytesIO(metadata_bytes)
        file_data = {
            "md5": hash_generator(metadata_bytes, 'md5'),
            "name": file_name,
            "size": len(metadata_bytes)}
    else:
        virtual_file = file
        file_data = {
            "md5": hash_generator(file.read(), 'md5'),
            "name": file_name,
            "size": os.path.getsize(os.path.join(path, file_name))}

    upload_response = requests.post(
        "https://api.figshare.com/v2/account/articles/{}/files".format(article_id), headers=headers, data=json.dumps(file_data))
    if upload_response.status_code != 201:
        raise PresQTResponseException(
            "FigShare returned an error trying to upload {}. Some items may still have been created on FigShare.".format(
                file_name),
            status.HTTP_400_BAD_REQUEST)

    # Get location information
    file_url = upload_response.json()['location']
    get_upload_response = requests.get(file_url, headers=headers).json()
    upload_url = get_upload_response['upload_url']
    file_id = get_upload_response['id']

    # Get upload information
    file_upload_response = requests.get(upload_url, headers=headers).json()
    upload_parts(headers, upload_url,
                 file_upload_response['parts'], virtual_file)

    complete_upload = requests.post(
        "https://api.figshare.com/v2/account/articles/{}/files/{}".format(
            article_id, file_id),
        headers=headers)

    if complete_upload.status_code != 202:
        raise PresQTResponseException(
            "FigShare returned an error trying to upload {}. Some items may still have been created on FigShare.".format(
                file_name),
            status.HTTP_400_BAD_REQUEST)
