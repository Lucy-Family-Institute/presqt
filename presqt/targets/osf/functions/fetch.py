import requests

from rest_framework import status

from presqt.targets.osf.utilities import get_osf_resource
from presqt.targets.osf.utilities.utils.get_page_numbers import get_page_numbers
from presqt.utilities import PresQTResponseException, PresQTInvalidTokenError, PresQTValidationError
from presqt.targets.osf.classes.main import OSF


def osf_fetch_resources(token, query_parameter, process_info_path):
    """
    Fetch all OSF resources for the user connected to the given token.

    Parameters
    ----------
    token : str
        User's OSF token
    query_parameter : dict
        The search parameter passed to the API View
        Gets passed formatted as {'title': 'search_info'}
    process_info_path: str
        Path to the process info file that keeps track of the action's progress

    Returns
    -------
    List of dictionary objects that represent OSF resources.
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
            "per_page": 10
        }
    """
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    pages = {
        "first_page": '1',
        "previous_page": None,
        "next_page": None,
        "last_page": '1',
        "total_pages": '1',
        "per_page": 10}
        
    if 'title' in query_parameter:
        # Format the search that is coming in to be passed to the OSF API
        query_parameters = query_parameter['title'].replace(' ', '+')
        url = 'https://api.osf.io/v2/nodes/?filter[title]={}'.format(query_parameters)
        if 'page' in query_parameter:
            url = 'https://api.osf.io/v2/nodes/?filter[title]={}&page={}'.format(
                query_parameters, query_parameter['page'])

    elif 'id' in query_parameter:
        url = 'https://api.osf.io/v2/nodes/?filter[id]={}'.format(query_parameter['id'])

    elif 'author' in query_parameter:
        query_parameters = query_parameter['author'].replace(' ', '+')
        user_url = 'https://api.osf.io/v2/users/?filter[full_name]={}'.format(query_parameters)
        if 'page' in query_parameter:
            user_url = 'https://api.osf.io/v2/users/?filter[full_name]={}&page={}'.format(
                query_parameters, query_parameter['page'])
        user_data = requests.get(user_url, headers={'Authorization': 'Bearer {}'.format(token)})
        if user_data.status_code != 200 or len(user_data.json()['data']) == 0:
            return [], pages
        else:
            url = user_data.json()[
                'data'][0]['relationships']['nodes']['links']['related']['href']

    elif 'keywords' in query_parameter:
        query_parameters = query_parameter['keywords'].replace(' ', '+')
        url = 'https://api.osf.io/v2/nodes/?filter[tags][icontains]={}'.format(query_parameters)
        if 'page' in query_parameter:
            url = 'https://api.osf.io/v2/nodes/?filter[tags][icontains]={}&page={}'.format(
                query_parameters, query_parameter['page'])

    elif 'page' in query_parameter:
        url = 'https://api.osf.io/v2/users/me/nodes?page={}'.format(query_parameter['page'])

    else:
        url = "https://api.osf.io/v2/users/me/nodes?page=1"
    
    try:
        resources = osf_instance.get_resources(process_info_path, url)
        pages = get_page_numbers(url, token)
    except PresQTValidationError as e:
        raise e

    return resources, pages


def osf_fetch_resource(token, resource_id):
    """
    Fetch the OSF resource matching the resource_id given.

    Parameters
    ----------
    token : str
        User's OSF token

    resource_id : str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the OSF resource.
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
            "sha256": "ea94ce54261720c16abb508c6dcd1fd481c30c09b7f2f5ab0b79e3199b7e2b55"
        },
        "extra": {
            "any": "extra",
            "values": "here"
        }
    }
    """
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    def create_object(resource_object):
        resource_object_obj = {
            'kind': resource_object.kind,
            'kind_name': resource_object.kind_name,
            'id': resource_object.id,
            'title': resource_object.title,
            'date_created': resource_object.date_created,
            'date_modified': resource_object.date_modified,
            'hashes': {
                'md5': resource_object.md5,
                'sha256': resource_object.sha256
            },
            'extra': {},
            "children": []
        }

        if resource_object.kind_name in ['folder', 'file']:
            resource_object_obj['extra'] = {
                'last_touched': resource_object.last_touched,
                'materialized_path': resource_object.materialized_path,
                'current_version': resource_object.current_version,
                'provider': resource_object.provider,
                'path': resource_object.path,
                'current_user_can_comment': resource_object.current_user_can_comment,
                'guid': resource_object.guid,
                'checkout': resource_object.checkout,
                'tags': resource_object.tags,
                'size': resource_object.size
            }
        elif resource_object.kind_name == 'project':
            resource_object_obj['extra'] = {
                'category': resource_object.category,
                'fork': resource_object.fork,
                'current_user_is_contributor': resource_object.current_user_is_contributor,
                'preprint': resource_object.preprint,
                'current_user_permissions': resource_object.current_user_permissions,
                'custom_citation': resource_object.custom_citation,
                'collection': resource_object.collection,
                'public': resource_object.public,
                'subjects': resource_object.subjects,
                'registration': resource_object.registration,
                'current_user_can_comment': resource_object.current_user_can_comment,
                'wiki_enabled': resource_object.wiki_enabled,
                'node_license': resource_object.node_license,
                'tags': resource_object.tags,
                'size': resource_object.size
            }
        return resource_object_obj

    # Get the resource
    resource = get_osf_resource(resource_id, osf_instance)

    return create_object(resource)
