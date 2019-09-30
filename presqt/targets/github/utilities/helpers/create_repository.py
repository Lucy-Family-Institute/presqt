import json
import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def create_repository(title, token, count=0):
    """
    Create a GitHub repository.

    Parameters
    ----------
    title : str
        The title of the repo being created
    token : str
        The users GitHub API token.
    """
    repository_payload = {"name": title}
    response = requests.post('https://api.github.com/user/repos?access_token={}'.format(token),
                             data=json.dumps(repository_payload))

    if response.status_code == 201:
        return title

    elif response.status_code == 422:
        # Handling Project Duplication
        count += 1
        if '-PresQT{}-'.format(count-1) in title[len(title)-9:]:
            title = title[:-2] + (str(count)+'-')
        else:
            title = title + '-PresQT{}-'.format(count)
        return create_repository(title, token, count)

    else:
        raise PresQTResponseException(
            "Response has status code {} while creating repository {}".format(response.status_code,
                                                                              title),
            status.HTTP_400_BAD_REQUEST)
