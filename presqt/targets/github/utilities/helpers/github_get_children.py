import urllib.parse
import requests


def github_get_children(data, header, parent_id, repo_id):
    """
    Get the children of the requested resource. Only going down one level.

    Parameters
    ----------
    data : list or dict
        The repo path data
    header : dict
        The GitHub Authorization header
    parent_id : str
        The parent id of the children
    repo_id :  str
        The top level repo id
    
    Returns
    -------
        The children of the requested resource.
    """
    children = []

    if isinstance(data, dict):
        # Get the contents of the top level repo
        # Partition is to strip the extra from GitHub API links
        print(data['contents_url'])
        data = requests.get(data['contents_url'].partition('{+path}')[0], headers=header).json()

    for child in data:
        if child['type'] == 'dir':
            kind = 'container'
            kind_name = 'folder'
        else:
            kind = 'item'
            kind_name = 'file'

        formatted_id = '{}:{}'.format(repo_id, urllib.parse.quote_plus(
            child['path']).replace(".", "%252E").replace('%2F', '%252F').replace('%2E', '%252E'))

        children.append({
            "kind": kind,
            "kind_name": kind_name,
            "container": parent_id,
            "id": formatted_id,
            "title": child["name"]
        })

    return children
