import requests

def delete_users_projects(auth_token):
    """
    Deletes all of a given users projects on OSF.

    Warning: Mainly used for testing/Actions are irreversable
    
    Parameters
    ----------
    auth_token : str
        The Authorization Token of the requesting user.
    """
    headers = {'Authorization': 'Bearer {}'.format(auth_token)}
    response = requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()
    for node in response['data']:
        requests.delete('http://api.osf.io/v2/nodes/{}'.format(node['id']), headers=headers)
    next_url = response['links']['next']
    while next_url is not None:
        response_json = requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()
        for node in response_json['data']:
            requests.delete('http://api.osf.io/v2/nodes/{}'.format(node['id']), headers=headers)