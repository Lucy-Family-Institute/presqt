import json

import requests
from rest_framework import status

from presqt.utilities import PresQTResponseException


def create_repository(title, token):
    repository_payload = {"name": title}
    response = requests.post('https://api.github.com/user/repos?access_token={}'.format(token),
                             data=json.dumps(repository_payload))

    if response.status_code == 201:
        return response.json()

    elif response.status_code == 422:
        raise PresQTResponseException(
            "Repository, {},already exists on this account".format(title),
            status.HTTP_422_UNPROCESSABLE_ENTITY)

    else:
        raise PresQTResponseException(
            "Response has status code {} while creating repository {}".format(response.status_code,
                                                                              title),
            status.HTTP_400_BAD_REQUEST)
