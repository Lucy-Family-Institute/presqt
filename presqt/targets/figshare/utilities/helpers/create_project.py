import json
import requests

from rest_framework import status

from presqt.targets.utilities import get_duplicate_title
from presqt.utilities import PresQTResponseException


def create_project(project_title, headers, token):
    """
    Create a FigShare repository.

    Parameters
    ----------
    project_title : str
        The title of the project being created
    headers : dict
        The users FigShare Auth header
    token : str
        The users Auth token
    """
    project_payload = {"title": project_title}
    response = requests.post(
        "https://api.figshare.com/v2/account/projects",
        headers=headers,
        data=json.dumps(project_payload))

    if response.status_code == 201:
        # The second item returned is the project id.
        return project_title, response.json()['location'].rpartition('/')[2]

    elif response.status_code == 400:
        from presqt.targets.figshare.functions.fetch import figshare_fetch_resources
        # Get all the project titles
        figshare_resources = figshare_fetch_resources(token, None)

        titles = [data['title'] for data in figshare_resources if data['kind_name'] == 'project']
        title = get_duplicate_title(project_title, titles, '(PresQT*)')

        return create_project(title, headers, token)

    else:
        raise PresQTResponseException(
            "Response has status code {} while creating project {}".format(response.status_code,
                                                                           project_title),
            status.HTTP_400_BAD_REQUEST)
