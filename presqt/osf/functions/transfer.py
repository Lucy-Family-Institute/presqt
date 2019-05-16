from rest_framework import status

from presqt.exceptions import PresQTResponseException
from presqt.osf.classes.main import OSF
from presqt.osf.exceptions import OSFNotFoundError


def osf_download_resource(token, resource_id):
    """

    Parameters
    ----------
    token
    resource_id

    Returns
    -------

    """

    osf_instance = OSF(token)

    try:
        resource = osf_instance.resource(resource_id)
    except OSFNotFoundError:
        raise PresQTResponseException(
            "Resource with id '{}' not found for this user.".format(resource_id),
            status.HTTP_400_BAD_REQUEST)

    if resource.kind_name != 'file':
        raise PresQTResponseException(
            "Resource with id, '{}', is not a file.".format(resource_id),
            status.HTTP_400_BAD_REQUEST)

    resource_obj = {
        'title': resource.title,
        'id': resource.id,
        'kind': resource.kind,
        'kind_name': resource.kind_name,
        'hashes': {
            'sha256': resource.sha256,
            'md5': resource.md5
        },
        'path': resource.path,
        'download_url': resource.download_url
    }

    return resource_obj