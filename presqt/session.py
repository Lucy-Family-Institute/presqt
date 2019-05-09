import requests

from presqt.exceptions import PresQTInvalidTokenError


class PresQTSession(requests.Session):
    """
    Class that represents a session used to make repeated calls to an API.
    Subclasses Request Session class.
    """
    auth = None
    __attrs__ = requests.Session.__attrs__ + ['base_url']

    def __init__(self, base_url):
        """
        Handle HTTP session related work.

        Parameters
        ----------
        base_url : str
            Base URL for the API

        """
        super(PresQTSession, self).__init__()
        self.base_url = base_url

    def token_auth(self, token):
        """
        Add the user's API token to the header for authorization.

        Parameters
        ----------
        token : str
            User's token
        """
        self.headers.update({'Authorization': 'Bearer {}'.format(token)})

    def build_url(self, *args):
        """
        Takes in a list of arguments and uses them to build a
        url that gets appended to the base url.

        *args = ['me', 'nodes'] will build 'https:<base_url>/v2/me/nodes/'
        """
        parts = [self.base_url]
        parts.extend(args)
        # canonical URLs end with a slash
        return '/'.join(parts) + '/'

    def get(self, url, *args, **kwargs):
        """
        Make a GET request using the base request GET method with the provided url and arguments.

        Parameters
        ----------
        url : str
            URL the GET request should hit.

        Returns
        -------
            Response object.
        """

        response = super(PresQTSession, self).get(url, *args, **kwargs)
        if response.status_code == 401:
            raise PresQTInvalidTokenError("Token is invalid. Response returned a 401 status code.")
        return response