import json
import requests

from rest_framework import status

from presqt.targets.curate_nd.classes.main import CurateND
from presqt.utilities import (PresQTResponseException,
                              PresQTValidationError,
                              PresQTInvalidTokenError)


def curate_nd_upload_metadata(token, project_id, metadata_dict):
    """
    Upload the metadata of this PresQT action at the top level of the project.

    Parameters
    ----------
    token : str
        The user's CurateND token
    project_id : str
        The id of the top level project that the upload took place on
    metadata_dict : dict
        The metadata to be written to the repo
    """
    try:
        CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTValidationError("Token is invalid. Response returned a 401 status code.",
                                    status.HTTP_401_UNAUTHORIZED)

    header = {'X-Api-Token': token, 'Content-Type': 'application/x-www-form-urlencoded'}
    metadata_bytes = json.dumps(metadata_dict, indent=4).encode('utf-8')
    post_url = 'https://curatepprd.library.nd.edu/api/uploads/{}/file/new?file_name={}'.format(
        project_id, 'PRESQT_FTS_METADATA.json')

    response = requests.post(post_url, headers=header, data=metadata_bytes)
    print('POST METADATA')
    print(response.status_code)
    print(response.json())
    print('\n')
    if response.status_code != 200:
        raise PresQTResponseException(
            "CurateND returned an error trying to upload {}".format('PRESQT_FTS_METADATA.json'),
            status.HTTP_400_BAD_REQUEST)

    # Because of the way CurateNDs API is handling upload, we have to make the final commit here
    # instead of back in the main upload function.
    commit = requests.post(
        'https://curatepprd.library.nd.edu/api/uploads/{}/commit'.format(project_id),
        headers={'X-Api-Token': token})
    
    print('COMMIT', commit.json())

    if commit.status_code != 200:
        raise PresQTResponseException(
            "CurateND returned an error trying to commit this project.",
            status.HTTP_400_BAD_REQUEST)
