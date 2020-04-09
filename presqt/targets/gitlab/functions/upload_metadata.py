import base64
import json

import requests

from presqt.targets.gitlab.utilities import validation_check
from presqt.utilities import PresQTError


def gitlab_upload_metadata(token, project_id, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the repo.

    Parameters
    ----------
    token : str
        The user's GitLab token
    project_id : str
        The id of the top level project that the upload took place on
    metadata_dict : dict
        The metadata to be written to the repo
    """
    headers, user_id = validation_check(token)
    metadata_bytes = json.dumps(metadata_dict, indent=4).encode('utf-8')
    base64_metadata = base64.b64encode(metadata_bytes)

    post_url = "https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA%2Ejson".format(project_id)

    data = {"branch": "master",
            "commit_message": "PresQT Metadata Upload",
            "encoding": "base64",
            "content": base64_metadata}

    response = requests.post(post_url, headers=headers, data=data)

    if response.status_code != 201:
        raise PresQTError(
            "The request to create a metadata file has resulted in a {} error code from GitLab.".format(
                response.status_code))