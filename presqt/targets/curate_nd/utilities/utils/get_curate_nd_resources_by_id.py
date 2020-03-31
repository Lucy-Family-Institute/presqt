import requests


def get_curate_nd_resources_by_id(token, resource_id):
    """
    This function is used to retrieve resources when a user searches by id.

    Parameters
    ----------
    token : str
        User's CurateND token
    resource_id: str
        The resource id that the user is searching for

    Returns
    -------
    A list containing the item and it's files.
    """
    response = requests.get('https://curate.nd.edu/api/items/{}'.format(resource_id),
                            headers={'X-Api-Token': '{}'.format(token)})

    if response.status_code != 200:
        # We didn't find the resource.
        return []

    data = response.json()
    resources = [{
        "kind": "container",
        "kind_name": "item",
        "id": data['id'],
        "container": None,
        "title": data['title']}]

    for file in data['containedFiles']:
        resources.append({
            "kind": "item",
            "kind_name": "file",
            "id": file['id'],
            "container": data['id'],
            "title": file['label']})

    return resources
