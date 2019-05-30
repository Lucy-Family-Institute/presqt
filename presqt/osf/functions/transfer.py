from rest_framework import status

from presqt.exceptions import PresQTResponseException, PresQTInvalidTokenError
from presqt.osf.classes.main import OSF
from presqt.osf.helpers import get_osf_resource


def osf_download_resource(token, resource_id):
    """
    Fetch the requested resource from OSF along with it's class representation.

    Parameters
    ----------
    token : str
        User's OSF token.

    resource_id : str
        ID of the resource requested.

    Returns
    -------

    """

    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    # Get the resource
    resource = get_osf_resource(resource_id, osf_instance)

    files = []
    if resource.kind_name == 'file':
        binary_file = resource.download()
        files.append({
            'file': binary_file,
            'hashes': resource.hashes,
            'title': resource.title,
            # If the file is the only resource we are downloading then we don't need it's full path
            'path': '/{}'.format(resource.title)
        })
    else:
        for file in resource.get_all_files():
            # Calculate the full file path
            if resource.kind_name == 'project':
                file_path = '/{}/{}/{}'.format(resource.title,
                                               file.provider, file.materialized_path)
            elif resource.kind_name == 'storage':
                file_path = '/{}/{}'.format(file.provider, file.materialized_path)
            else:
                path_to_strip = resource.materialized_path[:-(len(resource.title)+2)]
                file_path = file.materialized_path[len(path_to_strip):]

            # binary_file = file.download()
            files.append({
                # 'file': binary_file,
                'hashes': file.hashes,
                'title': file.title,
                'path': file_path
            })
    return files