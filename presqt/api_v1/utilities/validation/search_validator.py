import re

from rest_framework import status

from presqt.utilities import PresQTResponseException


def search_validator(search_parameter):
    """
    Ensure the query parameter passed into the API view is valid.

    Parameters
    ----------
    search_parameter : dict
        The query parameter passed to the view.
    """
    # Check that the search query only has one key.
    if len(search_parameter.keys()) > 1:
        raise PresQTResponseException('The search query is not formatted correctly.',
                                      status.HTTP_400_BAD_REQUEST)

    # Check that the query parameter has `title`
    try:
        search_parameter['title']
    except KeyError:
        raise PresQTResponseException('The search query is not formatted correctly.',
                                      status.HTTP_400_BAD_REQUEST)

    # Ensure that there are no special characters in the search.
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    if (regex.search(search_parameter['title']) is not None):
        raise PresQTResponseException('The search query is not formatted correctly.',
                                      status.HTTP_400_BAD_REQUEST)
