import asyncio

import aiohttp
from rest_framework import status

from presqt.targets.osf.utilities import OSFForbiddenError, OSFNotFoundError
from presqt.targets.utilities import get_page_total, run_urls_async
from presqt.utilities import PresQTResponseException
from presqt.targets.utilities.utils.session import PresQTSession


class OSFBase(object):
    """
    Base class for all OSF classes and the main OSF object.
    """
    def __init__(self, json, session=None):
        # Set the session attribute with the existing session or a new one if one doesn't exist.
        if session is None:
            self.session = PresQTSession('https://api.osf.io/v2')
        else:
            self.session = session

    def _json(self, response):
        """
        Extract JSON from response.
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
        # Get initial data
        response_json = self._json(self.get(url))
        data = response_json['data']
        meta = response_json['links']['meta']

        # Calculate pagination pages
        if 'me' in url:
            page_total = get_page_total(meta['total'], meta['per_page'])
        else:
            page_total = 2
        url_list = ['{}?page={}'.format(url, number) for number in range(2, page_total)]

        # Call all pagination pages asynchronously
        children_data = run_urls_async(self, url_list)
        [data.extend(child['data']) for child in children_data]
        return data

    @staticmethod
    def _get_follow_next_urls(data_list):
        """
        Get a list of 'next' urls to run asynchronously.

        Parameters
        ----------
        data_list: list
            List of json data.

        Returns
        -------
        List of urls
        """
        url_list = []
        for data in data_list:
            meta = data['links']['meta']
            next_url = data['links']['next']
            if next_url:
                page_total = get_page_total(meta['total'], meta['per_page'])
                [url_list.append('{}{}'.format(
                    next_url[:-1], number)) for number in range(2, page_total + 1)]
        return url_list

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
        elif response.status_code == 410:
            raise PresQTResponseException("The requested resource is no longer available.", status.HTTP_410_GONE)
        elif response.status_code == 404:
            raise OSFNotFoundError("Resource not found.", status.HTTP_404_NOT_FOUND)
        elif response.status_code == 403:
            raise OSFForbiddenError(
                "User does not have access to this resource with the token provided.", status.HTTP_403_FORBIDDEN)


    def put(self, url, *args, **kwargs):
        """
        Handle any errors that may pop up while making PUT requests through the session.

        Parameters
        ----------
        url: str
            URL to make the PUT request to.

        Returns
        -------
        HTTP Response object

        """
        response = self.session.put(url, *args, **kwargs)
        return response

    def post(self, url, *args, **kwargs):
        """
        Handle any errors that may pop up while making POST requests through the session.

        Parameters
        ----------
        url: str
            URL to make the POST request to.

        Returns
        -------
        HTTP Response object
        """
        response = self.session.post(url, *args, **kwargs)
        return response
