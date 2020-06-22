import requests
from rest_framework import status

from presqt.targets.figshare.utilities.validation_check import validation_check
from presqt.targets.figshare.utilities.get_figshare_project_data import get_figshare_project_data
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
        raise PresQTResponseException("Figshare does not support search",
                                      status.HTTP_404_BAD_REQUEST)

    response_data = requests.get("https://api.figshare.com/v2/account/projects",
                                 headers=headers).json()

    return get_figshare_project_data(response_data, headers, [])
