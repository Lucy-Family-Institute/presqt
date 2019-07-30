from rest_framework import status

from presqt.exceptions import PresQTResponseException, PresQTInvalidTokenError
from presqt.osf.classes.main import OSF
from presqt.osf.helpers import get_osf_resource


def osf_download_resource(token, resource_id):
    """
    Fetch the requested resource from OSF along with its hash information.

    Parameters
    ----------
    token : str
        User's OSF token.

    resource_id : str
        ID of the resource requested.

    Returns
    -------
    List of dictionary objects that each hold a file and its information.
    """
    try:
        osf_instance = OSF(token)
    except PresQTInvalidTokenError:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)
    # Get the resource
    resource = get_osf_resource(resource_id, osf_instance)
    # Get all files for the provided resources.
    # The 'path' value will be the path that the file is eventually saved in. The root of the
    # path should be the resource.
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
            # Calculate the full file path with the resource as the root of the path.
            if resource.kind_name == 'project':
                # File path needs the project and storage names prepended to it.
                file_path = '/{}/{}/{}'.format(resource.title,
                                               file.provider, file.materialized_path)
            elif resource.kind_name == 'storage':
                # File path needs the storage name prepended to it.
                file_path = '/{}/{}'.format(file.provider, file.materialized_path)
            else: # elif project
                # File Path needs to start at the folder and strip everything before it.
                # Example: If the resource is 'Docs2' and the starting path is
                # '/Project/Storage/Docs1/Docs2/file.jpeg' then the final path
                # needs to be '/Docs2/file.jpeg'
                path_to_strip = resource.materialized_path[:-(len(resource.title)+2)]
                file_path = file.materialized_path[len(path_to_strip):]

            binary_file = file.download()
            files.append({
                'file': binary_file,
                'hashes': file.hashes,
                'title': file.title,
                'path': file_path
            })
    return files