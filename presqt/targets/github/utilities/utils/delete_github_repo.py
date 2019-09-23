import requests


def delete_github_repo(username, repo_name, header):
    """
    Delete a given repo for the user.

    Parameters
    ----------
    username : str
        The user's GitHub username
    repo_name : str
        The name of the repo to be deleted.
    header : dict
        The GitHub Authorization header.
    """
    delete_url = 'https://api.github.com/repos/{}/{}'.format(username, repo_name)

    requests.delete(delete_url, headers=header)