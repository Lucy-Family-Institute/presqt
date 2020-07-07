import requests
import itertools

from rest_framework import status

from presqt.json_schemas.schema_handlers import schema_validator
from presqt.targets.figshare.utilities.helpers.upload_helpers import figshare_file_upload_process
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
                        figshare_file_upload_process(
                            updated_metadata, headers, "INVALID_PRESQT_FTS_METADATA.json", article['id'])
                        # Add new metadata file
                        figshare_file_upload_process(
                            metadata_dict, headers, "PRESQT_FTS_METADATA.json", article['id'])
                        return

                    # Loop through each 'action' in both metadata files and make a new list of them.
                    joined_actions = [entry for entry in itertools.chain(metadata_dict['actions'],
                                                                         updated_metadata['actions'])]
                    joined_keywords = [entry for entry in itertools.chain(metadata_dict['allKeywords'],
                                                                          updated_metadata['allKeywords'])]
                    updated_metadata['actions'] = joined_actions
                    updated_metadata['allKeywords'] = list(set(joined_keywords))

                    figshare_file_upload_process(updated_metadata, headers,
                                                 "PRESQT_FTS_METADATA.json", article['id'])
                    return

    # Make a PRESQT_FTS_METADATA article...
    article_id = create_article("PRESQT_FTS_METADATA", headers, split_id[0])

    # New Metadata file
    figshare_file_upload_process(metadata_dict, headers, file_name, article_id)
