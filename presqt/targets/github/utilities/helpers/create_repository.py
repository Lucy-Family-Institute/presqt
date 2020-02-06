import fnmatch
import json
import re
import requests

from natsort import natsorted
from rest_framework import status

from presqt.targets.utilities import get_duplicate_title
from presqt.utilities import PresQTResponseException


def create_repository(title, token):
    """
    Create a GitHub repository.

    Parameters
    ----------
    title : str
        The title of the repo being created
    token : str
        The users GitHub API token.
    """
    header = {"Authorization": "token {}".format(token)}
    repository_payload = {"name": title}
    response = requests.post('https://api.github.com/user/repos'.format(token),
                             headers=header,
                             data=json.dumps(repository_payload))

    if response.status_code == 201:
        return title

    elif response.status_code == 422:
        # This is a little gross, but there isn't a better way to do it that I'm aware of.
        from presqt.targets.github.utilities import github_paginated_data

        titles = [data['name'] for data in github_paginated_data(token)]
        title = get_duplicate_title(title, titles, '-PresQT*-')

        return create_repository(title, token)

    else:
        raise PresQTResponseException(
            "Response has status code {} while creating repository {}".format(response.status_code,
                                                                              title),
            status.HTTP_400_BAD_REQUEST)
