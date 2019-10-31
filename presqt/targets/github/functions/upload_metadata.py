import base64
import json
import requests

from rest_framework import status

from presqt.targets.github.utilities import validation_check
from presqt.utilities import PresQTError, PresQTResponseException


def github_upload_metadata(token, resource_id, metadata_dict, repo_id=None):
    """
    Upload the metadata of this PresQT action at the top level of the repo.

    Parameters
    ----------
    token : str
        The user's GitHub token
    resource_id : str
        An id the upload is taking place on (not used for GitHub)
    metadata_dict : dict
        The metadata to be written to the repo
    repo_id : str
        The id of the new repo that has been created
    """
    header, username = validation_check(token)

    file_name = "PRESQT_FTS_METADATA.json"

    metadata_bytes = json.dumps(metadata_dict, indent=4).encode('utf-8')
    base64_metadata = base64.b64encode(metadata_bytes).decode('utf-8')

    put_url = "https://api.github.com/repos/{}/{}/contents/{}".format(username, repo_id, file_name)

    data = {
        "message": "PresQT Upload",
        "committer": {
            "name": "PresQT",
            "email": "N/A"},
        "content": base64_metadata}

    response = requests.put(put_url, headers=header, data=json.dumps(data))

    if response.status_code != 201:
        raise PresQTError(
            "The request to create a metadata file has resulted in a {} error code from GitHub.".format(
                response.status_code))
