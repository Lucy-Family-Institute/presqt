import json
import requests

from rest_framework import status

from presqt.utilities import PresQTResponseException


def create_article(article_title, headers, project_id):
    """
    Create a FigShare article.

    Parameters
    ----------
    article_title : str
        The title of the project being created
    headers : dict
        The users FigShare Auth header
    """
    article_payload = {"title": article_title}

    response = requests.post(
        "https://api.figshare.com/v2/account/projects/{}/articles".format(project_id),
        headers=headers,
        data=json.dumps(article_payload)
    )

    if response.status_code != 201:
        raise PresQTResponseException(
            "Response has status code {} while creating article {}".format(response.status_code,
                                                                           article_title),
            status.HTTP_400_BAD_REQUEST)

    article_response = requests.get(response.json()['location'], headers=headers).json()

    return article_response['id']
