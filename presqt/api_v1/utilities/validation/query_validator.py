import re

from rest_framework import status

from presqt.api_v1.utilities.utils.get_target_data import get_target_data
from presqt.utilities import PresQTResponseException


def query_validator(query_parameter, target_name):
    """
    Ensure the query parameter passed into the API view is valid.

    Parameters
    ----------
    query_parameter : dict
        The query parameter passed to the view.
    target_name : str
        The name of the target.
    """
    # Check that the search query only has one key.
    if len(query_parameter.keys()) > 1:
        raise PresQTResponseException('PresQT Error: The search query is not formatted correctly.',
                                      status.HTTP_400_BAD_REQUEST)
    if list(query_parameter.keys())[0] == 'page':
        try:
            int(list(query_parameter.values())[0])
        except ValueError:
            raise PresQTResponseException('PresQT Error: The page query is not formatted correctly. Page specified must be a number.',
                                          status.HTTP_400_BAD_REQUEST)
        else:
            return list(query_parameter.values())[0]
    else:
        target_data = get_target_data(target_name)
        list_of_search_params = target_data['search_parameters']
        # Check that the query parameter is in list of accepted searches
        if list(query_parameter.keys())[0] not in list_of_search_params:
            raise PresQTResponseException('PresQT Error: {} does not support {} as a search parameter.'.format(
                target_data['readable_name'], list(query_parameter.keys())[0]),
                status.HTTP_400_BAD_REQUEST)

        # Ensure that there are no special characters in the search.
        regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')

        if 'title' in query_parameter:
            if (regex.search(query_parameter['title']) is not None):
                raise PresQTResponseException('PresQT Error: The search query is not formatted correctly.',
                                              status.HTTP_400_BAD_REQUEST)
        return list(query_parameter.values())[0]
