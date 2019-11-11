import requests

from rest_framework import status

from presqt.targets.zenodo.utilities import zenodo_validation_check
from presqt.utilities import PresQTValidationError, PresQTResponseException


def zenodo_fetch_resources(token):
    """
    Fetch all users repos from Zenodo.

    Parameters
    ----------
    token : str
            User's Zenodo token

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
        raise PresQTValidationError("Zenodo returned a 401 unauthorized status code.",
                                    status.HTTP_401_UNAUTHORIZED)

    # Let's build them resources
    base_url = "https://zenodo.org/api/deposit/depositions"
    zenodo_projects = requests.get(base_url, params=auth_parameter).json()

    resources = []
    for entry in zenodo_projects:
        resource = {
            "kind": "container",
            "kind_name": entry['metadata']['upload_type'],
            "container": None,
            "id": entry['id'],
            "title": entry['metadata']['title']}
        resources.append(resource)
        for item in requests.get(entry['links']['files'], params=auth_parameter).json():
            resource = {
                "kind": "item",
                "kind_name": "file",
                "container": entry['id'],
                "id": item['id'],
                "title": item['filename']}
            resources.append(resource)

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
        raise PresQTValidationError("Zenodo returned a 401 unauthorized status code.",
                                    status.HTTP_401_UNAUTHORIZED)

    base_url = "https://zenodo.org/api/deposit/depositions"
    zenodo_projects = requests.get(base_url, params=auth_parameter).json()

    if len(resource_id) > 7:
        for entry in zenodo_projects:
            project_files = requests.get(entry['links']['self'], params=auth_parameter).json()
            for entry in project_files['files']:
                if entry['id'] == resource_id:
                    resource = {
                        "kind": "item",
                        "kind_name": "file",
                        "id": resource_id,
                        "title": entry['filename'],
                        "date_created": None,
                        "date_modified": None,
                        "hashes": {
                            "md5": entry['checksum']
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

    else:
        for entry in zenodo_projects:
            if str(entry['id']) == resource_id:
                resource = {
                    "kind": "container",
                    "kind_name": entry['metadata']['upload_type'],
                    "id": entry['id'],
                    "title": entry['metadata']['title'],
                    "date_created": entry['created'],
                    "date_modified": entry['modified'],
                    "hashes": {},
                    "extra": {}
                }
                for key, value in entry.items():
                    resource['extra'][key] = value
                break
        else:
            raise PresQTResponseException("The resource could not be found by the requesting user.",
                                          status.HTTP_404_NOT_FOUND)

    return resource
