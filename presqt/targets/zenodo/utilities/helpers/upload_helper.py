import json
import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def zenodo_upload_helper(auth_parameter, project_title=None):
    """
    Initialize a new project on Zenodo.

    Parameters
    ----------
    auth_parameter : str
        The Authentication parameter expected by Zenodo.

    Returns
    -------
    The new Project ID and zenodo 'username'.
    """

    headers = {"Content-Type": "application/json"}

    project_info = requests.post('https://zenodo.org/api/deposit/depositions', params=auth_parameter,
                                 json={}, headers=headers)

    if project_info.status_code != 201:
        raise PresQTResponseException(
            "Zenodo returned a {} status code while trying to create the project.".format(
                project_info.status_code), status.HTTP_400_BAD_REQUEST)

    project_helper = project_info.json()
    project_id = project_helper['id']
    project_owner = project_helper['owner']

    # Now we need to add some info to the project.
    data = {
        'metadata': {
            'title': project_title,
            'upload_type': 'other',
            'description': 'PresQT Upload',
            'creators': [{'name': str(project_owner)}]}}

    requests.put('https://zenodo.org/api/deposit/depositions/{}'.format(project_id),
                 params=auth_parameter, data=json.dumps(data), headers=headers)

    return project_id, project_owner
