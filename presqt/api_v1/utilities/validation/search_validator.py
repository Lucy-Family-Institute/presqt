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
        raise PresQTResponseException('PresQT Error: The search query is not formatted correctly.',
                                      status.HTTP_400_BAD_REQUEST)

    list_of_search_params = ['id', 'title']
    # Check that the query parameter is in list of accepted searches
    if list(search_parameter.keys())[0] in list_of_search_params:
        pass
    else:
        raise PresQTResponseException('PresQT Error: The search query is not formatted correctly.',
                                      status.HTTP_400_BAD_REQUEST)

    # Ensure that there are no special characters in the search.
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')

    if 'title' in search_parameter:
        if (regex.search(search_parameter['title']) is not None):
            raise PresQTResponseException('PresQT Error: The search query is not formatted correctly.',
                                          status.HTTP_400_BAD_REQUEST)
