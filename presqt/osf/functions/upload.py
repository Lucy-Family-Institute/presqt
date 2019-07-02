import os

from rest_framework import status

from presqt.exceptions import PresQTInvalidTokenError, PresQTResponseException
from presqt.osf.classes.main import OSF
from presqt.osf.helpers import get_osf_resource


def osf_upload_resource(token, resource_id, resource_main_dir):
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    # Get the resource
    resource = get_osf_resource(resource_id, osf_instance)

    # Resource being uploaded to must not be a file
    if resource.kind_name == 'file':
        raise PresQTResponseException(
            "The Resource provided, {}, is not a container".format(resource_id),
            status.HTTP_401_UNAUTHORIZED)

    elif resource.kind == 'project':
        pass
    else:
        resource.create_directory(resource_main_dir)


    return