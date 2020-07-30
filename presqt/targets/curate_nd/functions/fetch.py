import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException, PresQTInvalidTokenError, PresQTValidationError
from presqt.targets.curate_nd.classes.main import CurateND
from presqt.targets.curate_nd.utilities import get_curate_nd_resource, get_curate_nd_resources_by_id, get_page_numbers


def curate_nd_fetch_resources(token, query_parameter):
    """
    Fetch all CurateND resources for the user connected to the given token.

    Parameters
    ----------
    token : str
        User's CurateND token
    query_parameter : dict
        The search parameter passed to the API View
        Gets passed formatted as {'title': 'search_info'}

    Returns
    -------
    List of dictionary objects that represent CurateND resources.
    Dictionary must be in the following format:
        {
            "kind": "container",
            "kind_name": "folder",
            "id": "12345",
            "container": "None",
            "title": "Folder Name",
        }
    We are also returning a dictionary of pagination information.
    Dictionary must be in the following format:
        {
            "first_page": '1',
            "previous_page": None,
            "next_page": None,
            "last_page": '1',
            "total_pages": '1',
            "per_page": 12
        }
    """
    try:
        curate_instance = CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException(
            "Token is invalid. Response returned a 401 status code.",
            status.HTTP_401_UNAUTHORIZED)

    pages = {
        "first_page": '1',
        "previous_page": None,
        "next_page": None,
        "last_page": '1',
        "total_pages": '1',
        "per_page": 12}

    if query_parameter:
        if 'title' in query_parameter:
            # Format the search that is coming in to be passed to the Curate API
            query_parameters = query_parameter['title'].replace(' ', '+')
            search_url = 'https://curate.nd.edu/api/items?q={}&search_fields=title'.format(
                query_parameters)
            try:
                resources = curate_instance.get_resources(search_url)
            except PresQTValidationError as e:
                raise e

        elif 'general' in query_parameter:
            search_url = 'https://curate.nd.edu/api/items?q={}'.format(query_parameter['general'])
            try:
                resources = curate_instance.get_resources(search_url)
            except PresQTValidationError as e:
                raise e

        elif 'id' in query_parameter:
            resources = get_curate_nd_resources_by_id(token, query_parameter['id'])

        elif 'page' in query_parameter:
            url = 'https://curate.nd.edu/api/items?editor=self&page={}'.format(query_parameter['page'])
            resources = curate_instance.get_resources(url)
            pages = get_page_numbers(url, token)
    else:
        url = 'https://curate.nd.edu/api/items?editor=self&page=1'
        resources = curate_instance.get_resources(url)
        pages = get_page_numbers(url, token)

    return resources, pages


def curate_nd_fetch_resource(token, resource_id):
    """
    Fetch the CurateND resource matching the resource_id given.

    Parameters
    ----------
    token : str
        User's CurateND token

    resource_id : str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the CurateND resource.
    Dictionary must be in the following format:
    {
        "kind": "item",
        "kind_name": "file",
        "id": "12345",
        "title": "23296359282_934200ec59_o.jpg",
        "date_created": "2019-05-13T14:54:17.129170Z",
        "date_modified": "2019-05-13T14:54:17.129170Z",
        "hashes": {
            "md5": "aaca7ef067dcab7cb8d79c36243823e4",
        },
        "extra": {
            "any": extra,
            "values": here
        }
    }
    """
    try:
        curate_instance = CurateND(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException(
            "Token is invalid. Response returned a 401 status code.",
            status.HTTP_401_UNAUTHORIZED,
        )
    # Get the resource
    resource = get_curate_nd_resource(resource_id, curate_instance)
    resource_dict = {
        "kind": resource.kind,
        "kind_name": resource.kind_name,
        "id": resource.id,
        "title": resource.title,
        "date_created": resource.date_submitted,
        "date_modified": resource.modified,
        "hashes": {"md5": resource.md5},
        "extra": resource.extra}

    return resource_dict
