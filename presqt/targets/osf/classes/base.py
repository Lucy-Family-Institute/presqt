import asyncio

import aiohttp
from rest_framework import status

from presqt.targets.utilities import get_page_total
from presqt.utilities import PresQTResponseException
from presqt.targets.osf.exceptions import OSFNotFoundError, OSFForbiddenError
from presqt.targets.utilities.session import PresQTSession


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

    def _follow_next(self, url):
        """
        Follow the 'next' link on paginated results.

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
        page_total = get_page_total(meta['total'], meta['per_page'])
        url_list = ['{}?page={}'.format(url, number) for number in range(2, page_total + 1)]

        # Call all pagination pages asynchronously
        children_data = self.run_urls_async(url_list)
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

    def run_urls_async(self, url_list):
        """
        Open an async loop and begin async calls.

        Parameters
        ----------
        url_list: list
            List of urls to call asynchronously

        Returns
        -------
        The data returned from the async call
        """
        loop = asyncio.new_event_loop()
        data = loop.run_until_complete(self.async_main(url_list))
        return data

    async def async_get(self, url, session):
        """
        Coroutine that uses aiohttp to make a GET request. This is the method that will be called
        asynchronously with other GETs.

        Parameters
        ----------
        url: str
            URL to call
        session: ClientSession object
            aiohttp ClientSession Object

        Returns
        -------
        Response JSON
        """
        async with session.get(url, headers=self.session.headers) as response:
            assert response.status == 200
            return await response.json()


    async def async_main(self, url_list):
        """
        Main coroutine method that will gather the url calls to be made and will make them
        asynchronously.

        Parameters
        ----------
        url_list: list
            List of urls to call

        Returns
        -------
        List of data brought back from each coroutine called.
        """
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*[self.async_get(url, session) for url in url_list])

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