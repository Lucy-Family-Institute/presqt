from rest_framework import status

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

        # Set the class attributes
        self._populate_attributes(json)

    def _populate_attributes(self, json):
        """
        Empty method expected to be overwritten in the subclass to add individual attributes
        to the class.
        """
        pass

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
        """
        response_json = self._json(self.session.get(url))
        data = response_json['data']

        next_url = response_json['links']['next']
        while next_url is not None:
            response_json = self._json(self.session.get(next_url))
            data.extend(response_json['data'])
            next_url = response_json['links']['next']

        return data
