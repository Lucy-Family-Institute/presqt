import requests


def delete_gitlab_project(project_id, token):
    """
    Delete the given project from Gitlab.

    Parameters
    ----------
    project_id: str
        The ID of the project to delete.
    token: str
        The user's GitLab token
    """
    headers = {"Private-Token": "{}".format(token)}

    requests.delete("https://gitlab.com/api/v4/projects/{}".format(project_id), headers=headers)