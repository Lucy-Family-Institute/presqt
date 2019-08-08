from rest_framework import status

from presqt.exceptions import PresQTResponseException
from presqt.osf.exceptions import OSFNotFoundError, OSFForbiddenError
from presqt.session import PresQTSession


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
        Extract JSON from response if `status_code` is 200.
        """
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            raise OSFForbiddenError(
                "User does not have access to this resource with the token provided.",
                status.HTTP_403_FORBIDDEN)
        elif response.status_code == 404:
            raise OSFNotFoundError(
                "Response has status code 404 not 200.", status.HTTP_404_NOT_FOUND)

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
        response_json = self._json(self.get(url))
        data = response_json['data']

        next_url = response_json['links']['next']
        while next_url is not None:
            response_json = self._json(self.get(next_url))
            data.extend(response_json['data'])
            next_url = response_json['links']['next']

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
        response =  self.session.get(url, *args, **kwargs)

        if response.status_code == 410:
            raise PresQTResponseException("The requested resource is no longer available.",
                                          status.HTTP_410_GONE)
        return response

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