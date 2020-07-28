import requests

from rest_framework import status

from presqt.targets.zenodo.utilities import (
    zenodo_validation_check, zenodo_fetch_resources_helper, zenodo_fetch_resource_helper)
from presqt.utilities import PresQTValidationError, PresQTResponseException


def zenodo_fetch_resources(token, search_parameter):
    """
    Fetch all users repos from Zenodo.

    Parameters
    ----------
    token : str
        User's Zenodo token
    search_parameter : dict
        The search parameter passed to the API View
        Gets passed formatted as {'title': 'search_info'}

    Returns
    -------
    List of dictionary objects that represent Zenodo resources.
    Dictionary must be in the following format
        {
            "kind": "container",
            "kind_name": "folder",
            "id": "12345",
            "container": "None",
            "title": "Folder Name"
        }
    """
    try:
        auth_parameter = zenodo_validation_check(token)
    except PresQTValidationError:
        raise PresQTValidationError("Token is invalid. Response returned a 401 status code.",
                                    status.HTTP_401_UNAUTHORIZED)
    # Let's build them resources
    if search_parameter and 'page' not in search_parameter:
        if 'title' in search_parameter:
            search_parameters = search_parameter['title'].replace(' ', '+')
            base_url = 'https://zenodo.org/api/records?q=title:"{}"&sort=most_recent'.format(
                search_parameters)

        elif 'id' in search_parameter:
            base_url = 'https://zenodo.org/api/records?q=conceptrecid:{}'.format(search_parameter['id'])

        elif 'general' in search_parameter:
            search_parameters = search_parameter['general'].replace(' ', '+')
            base_url = 'https://zenodo.org/api/records?q={}'.format(search_parameters)

        elif 'keywords' in search_parameter:
            search_parameters = search_parameter['keywords'].replace(' ', '+')
            base_url = 'https://zenodo.org/api/records?q=keywords:{}'.format(search_parameters)

        zenodo_projects = requests.get(base_url, params=auth_parameter).json()['hits']['hits']
        is_record = True

    else:
        if 'page' in search_parameter:
            base_url = "https://zenodo.org/api/deposit/depositions?page={}".format(search_parameter['page'])
        else:
            base_url = "https://zenodo.org/api/deposit/depositions?page=1"
        zenodo_projects = requests.get(base_url, params=auth_parameter).json()
        is_record = False

    resources = zenodo_fetch_resources_helper(zenodo_projects, auth_parameter, is_record)

    return resources


def zenodo_fetch_resource(token, resource_id):
    """
    Fetch the Zenodo resource matching the resource_id given.

    Parameters
    ----------
    token : str
        User's Zenodo token

    resource_id : str
        ID of the resource requested

    Returns
    -------
    A dictionary object that represents the Zenodo resource.
    Dictionary must be in the following format:
    {
        "kind": "container",
        "kind_name": "repo",
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
        auth_parameter = zenodo_validation_check(token)
    except PresQTValidationError:
        raise PresQTValidationError("Token is invalid. Response returned a 401 status code.",
                                    status.HTTP_401_UNAUTHORIZED)

    # Let's first try to get the record with this id.
    if len(str(resource_id)) <= 7:
        base_url = "https://zenodo.org/api/records/{}".format(resource_id)
        zenodo_project = requests.get(base_url, params=auth_parameter)
        if zenodo_project.status_code == 200:
            # We found the record, pass the project to our function.
            resource = zenodo_fetch_resource_helper(zenodo_project.json(), resource_id, True)
        else:
            # We need to get the resource from the depositions
            base_url = "https://zenodo.org/api/deposit/depositions/{}".format(resource_id)
            zenodo_project = requests.get(base_url, params=auth_parameter)
            if zenodo_project.status_code != 200:
                raise PresQTResponseException("The resource could not be found by the requesting user.",
                                              status.HTTP_404_NOT_FOUND)
            else:
                resource = zenodo_fetch_resource_helper(
                    zenodo_project.json(), resource_id, False, False)

    else:
        # We got ourselves a file.
        base_url = "https://zenodo.org/api/files/{}".format(resource_id)
        zenodo_project = requests.get(base_url, params=auth_parameter)
        if zenodo_project.status_code == 200:
            # Contents returns a list of the single file
            resource = zenodo_fetch_resource_helper(
                zenodo_project.json()['contents'][0], resource_id, True, True)
        else:
            # We need to loop through the users depositions and see if the file is there.
            base_url = 'https://zenodo.org/api/deposit/depositions'
            zenodo_projects = requests.get(base_url, params=auth_parameter).json()
            for entry in zenodo_projects:
                project_files = requests.get(entry['links']['self'], params=auth_parameter).json()
                for file in project_files['files']:
                    if file['id'] == resource_id:
                        resource = {
                            "container": entry['id'],
                            "kind": "item",
                            "kind_name": "file",
                            "id": resource_id,
                            "title": file['filename'],
                            "date_created": None,
                            "date_modified": None,
                            "hashes": {
                                "md5": file['checksum']
                            },
                            "extra": {}}
                        # We found the file, break out of file loop
                        break
                # If the file wasn't found, we want to continue looping through the other projects.
                else:
                    continue
                # File has been found, break out of project loop
                break

            # File not found, raise exception
            else:
                raise PresQTResponseException("The resource could not be found by the requesting user.",
                                              status.HTTP_404_NOT_FOUND)

    return resource
