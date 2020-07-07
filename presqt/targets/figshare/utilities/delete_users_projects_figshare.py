import requests

def delete_users_projects_figshare(auth_token):
    """
    Deletes all of a given users projects on FigShare.

    Warning: Mainly used for testing/Actions are irreversible

    Parameters
    ----------
    auth_token : str
        The Authorization Token of the requesting user.
    """
    headers = {'Authorization': 'token {}'.format(auth_token)}
    response_data = requests.get("https://api.figshare.com/v2/account/projects", headers=headers).json()
    for project_data in response_data:
        if project_data['title'] == 'NewProject':
            articles_response_data = requests.get(project_data['url']+ '/articles', headers=headers).json()
            for article_data in articles_response_data:
                requests.delete(article_data['url_private_api'], headers=headers)
            requests.delete(project_data['url'], headers=headers)

