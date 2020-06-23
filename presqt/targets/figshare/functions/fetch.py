import requests
from rest_framework import status

from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.targets.figshare.utilities.get_figshare_project_data import (
    get_figshare_project_data, get_search_project_data)
from presqt.utilities import PresQTResponseException


def figshare_fetch_resources(token, search_parameter):
    """
    Fetch all users projects from FigShare.

    Parameters
    ----------
    token : str
        User's FigShare token
    search_parameter : dict
        The search parameter passed to the API View
        Gets passed formatted as {'title': 'search_info'}

    Returns
    -------
    List of dictionary objects that represent FigShare resources.
    Dictionary must be in the following format:
        {
            "kind": "container",
            "kind_name": "folder",
            "id": "12345",
            "container": "None",
            "title": "Folder Name",
        }
    """
    base_url = "https://api.figshare.com/v2/"

    try:
        headers = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    if search_parameter:
        if 'id' in search_parameter:
            response = requests.get("{}projects/{}".format(base_url, search_parameter['id']))

        if response.status_code != 200:
            raise PresQTResponseException("Project with id, {}, can not be found.".format(search_parameter['id']),
                                          status.HTTP_404_NOT_FOUND)
        return get_search_project_data(response.json(), headers, [])

    else:
        response_data = requests.get("{}account/projects".format(base_url),
                                     headers=headers).json()

    return get_figshare_project_data(response_data, headers, [])
