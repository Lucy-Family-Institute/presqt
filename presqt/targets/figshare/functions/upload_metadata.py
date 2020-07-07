import io
import json
import requests
import itertools

from rest_framework import status

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.api_v1.utilities.fixity.hash_generator import hash_generator
from presqt.targets.figshare.functions.upload import upload_parts
from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.targets.figshare.utilities.helpers.create_article import create_article
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
    split_id = str(article_id).split(":")
    file_name = 'PRESQT_FTS_METADATA.json'

    # We need to check for a metadata article.
    article_list = requests.get(
        "https://api.figshare.com/v2/account/projects/{}/articles".format(split_id[0]),
        headers=headers).json()

    for article in article_list:
        if article['title'] == "PRESQT_FTS_METADATA":
            # Check for metadata file
            project_files = requests.get("{}/files".format(article['url']), headers=headers).json()
            for file in project_files:
                if file['name'] == "PRESQT_FTS_METADATA.json":
                    # Download file, delete old file, mixem up, have a time.
                    file_contents = requests.get(file['download_url'], headers=headers).json()
                    # Load the existing metadata to be updated.
                    updated_metadata = file_contents
                    requests.delete("https://api.figshare.com/v2/account/articles/{}/files/{}".format(
                        article['id'], file['id']),
                        headers=headers)

                    if schema_validator('presqt/json_schemas/metadata_schema.json', updated_metadata) is not True:
                        # Make old metadata invalid
                        metadata_file_upload_process(
                            updated_metadata, headers, "INVALID_PRESQT_FTS_METADATA.json", article['id'])
                        # Add new metadata file
                        metadata_file_upload_process(
                            metadata_dict, headers, "PRESQT_FTS_METADATA.json", article['id'])
                        return

                    # Loop through each 'action' in both metadata files and make a new list of them.
                    joined_actions = [entry for entry in itertools.chain(metadata_dict['actions'],
                                                                         updated_metadata['actions'])]
                    joined_keywords = [entry for entry in itertools.chain(metadata_dict['allKeywords'],
                                                                          updated_metadata['allKeywords'])]
                    updated_metadata['actions'] = joined_actions
                    updated_metadata['allKeywords'] = list(set(joined_keywords))

                    metadata_file_upload_process(updated_metadata, headers,
                                                 "PRESQT_FTS_METADATA.json", article['id'])
                    return

    # Make a PRESQT_FTS_METADATA article...
    article_id = create_article("PRESQT_FTS_METADATA", headers, split_id[0])

    # New Metadata file
    metadata_file_upload_process(metadata_dict, headers, file_name, article_id)


def metadata_file_upload_process(metadata_dict, headers, file_name, article_id):
    """
    This function covers the file upload process for FigShare.

    Parameters
    ----------
    metadata_dict: dict
        The metadata dictionary to writte to FigShare
    headers: dict
        The user's FigShare Auth header
    file_name: str
        The name of the file being uploaded
    article_id: str
        The id of the article to upload to
    """
    metadata_bytes = json.dumps(metadata_dict, indent=4).encode('utf-8')

    file_data = {
        "md5": hash_generator(metadata_bytes, 'md5'),
        "name": file_name,
        "size": len(metadata_bytes)}

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
    virtual_file = io.BytesIO(metadata_bytes)
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
