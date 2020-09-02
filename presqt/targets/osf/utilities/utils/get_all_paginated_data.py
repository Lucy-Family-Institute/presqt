import requests
from rest_framework import status

from presqt.targets.osf.utilities import OSFNotFoundError, OSFForbiddenError
from presqt.targets.utilities import get_page_total
from presqt.utilities import PresQTResponseException


def get_all_paginated_data(url, token):
    """
    Get all data for the requesting user.

    Parameters
    ----------
    url : str
        URL to the current data to get

    token: str
        User's OSF token

    Returns
    -------
    Data dictionary of the data points gathered up until now.
    """
    headers = {'Authorization': 'Bearer {}'.format(token)}
    # Get initial data
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
    elif response.status_code == 410:
        raise PresQTResponseException("The requested resource is no longer available.", status.HTTP_410_GONE)
    elif response.status_code == 404:
        raise OSFNotFoundError("Resource not found.", status.HTTP_404_NOT_FOUND)
    elif response.status_code == 403:
        raise OSFForbiddenError(
        "User does not have access to this resource with the token provided.", status.HTTP_403_FORBIDDEN)

    data = response_json['data']
    meta = response_json['links']['meta']

    # Calculate pagination pages
    if '?filter' in url or '?page' in url:
        # We already have all the data we need for this request
        return data
    else:
        page_total = get_page_total(meta['total'], meta['per_page'])
        url_list = ['{}?page={}'.format(url, number) for number in range(2, page_total + 1)]

    # Call all pagination pages asynchronously
    from presqt.targets.osf.utilities.utils.async_functions import run_urls_async
    children_data = run_urls_async(url_list, headers)
    [data.extend(child['data']) for child in children_data]

    return data