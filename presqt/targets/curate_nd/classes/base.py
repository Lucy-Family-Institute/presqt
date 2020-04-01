from rest_framework import status

from presqt.targets.curate_nd.utilities import (
    CurateNDNotFoundError, CurateNDForbiddenError, CurateNDServerError)
from presqt.targets.utilities import get_page_total, PresQTSession, run_urls_async


class CurateNDBase(object):
    """
    Base class for all Curate ND classes.
    """

    def __init__(self, json, session=None):
        # Set the session attribute with the existing session or a new one if one doesn't exist.
        if session is None:
            self.session = PresQTSession('https://curate.nd.edu/api/items')
        else:
            self.session = session

    def _json(self, response):
        """
        Extract JSON from response if status code == 200.
        """
        return response.json()

    def _get_all_paginated_data(self, url):
        """
        Get all data for the requesting user.

        Parameters
        ----------
        url : str
            URL to the current data to get

        Returns
        -------
        Data dictionary of the data points gathered up until now.
        """
        print(url)
        if url is None:
            url = 'https://curate.nd.edu/api/items?editor=self'
        # Get initial data
        response_json = self._json(self.get(url))
        data = response_json['results']
        pagination = response_json['pagination']

        # Calculate pagination pages
        if "?q" in url:
            page_total = 2
        else:
            page_total = get_page_total(pagination['totalResults'], pagination['itemsPerPage'])
        url_list = ['{}&page={}'.format(url, number) for number in range(2, page_total)]

        # Call all pagination pages asynchronously
        children_data = run_urls_async(self, url_list)           
        [data.extend(child['results']) for child in children_data]
        return data

    def get(self, url, *args, **kwargs):
        """
        Handle any errors that may pop up while making GET requests through the session.
        Parameters
        ----------
        url: str
            URL to make the GET request to.
        Returns
        -------
        HTTP Response object
        """
        response = self.session.get(url, *args, **kwargs)
        if response.status_code == 200:
            return response
        elif response.status_code == 403:
            raise CurateNDForbiddenError(
                "User does not have access to this resource with the token provided.",
                status.HTTP_403_FORBIDDEN)
        elif response.status_code == 404:
            raise CurateNDNotFoundError("Resource not found.", status.HTTP_404_NOT_FOUND)
        elif response.status_code == 500:
            raise CurateNDServerError(
                "CurateND returned a 500 server error.", status.HTTP_500_INTERNAL_SERVER_ERROR)
