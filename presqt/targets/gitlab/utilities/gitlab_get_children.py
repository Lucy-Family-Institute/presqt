import urllib.parse
import requests


def gitlab_get_children(data, resource_id, project_id):
    """
    Get the children of the requested resource. Only going down one level.

    Parameters
    ----------
    data : list or dict
        The project path data
    header : dict
        The GitLab Authorization header
    resource_id : str
        The resource id of the children
    project_id :  str
        The top level project id

    Returns
    -------
        The children of the requested resource.
    """
    children = []

    for child in data:
        if child['type'] == 'tree':
            kind = 'container'
            kind_name = 'folder'
        else:
            kind = 'item'
            kind_name = 'file'

        formatted_id = '{}:{}'.format(project_id, urllib.parse.quote_plus(
            child['path']).replace(".", "%252E").replace("/", "%252F").replace('%2F', '%252F').replace('%2E', '%252E'))

        children.append({
            "kind": kind,
            "kind_name": kind_name,
            "container": resource_id,
            "id": formatted_id,
            "title": child["name"]
        })

    return children
