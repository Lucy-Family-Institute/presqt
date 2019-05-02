import requests


class OSFSession(requests.Session):
    """
    Class that represents a session used to make repeated calls to the OSF API.
    Subclasses Request Session class.
    """
    auth = None
    __attrs__ = requests.Session.__attrs__ + ['base_url']

    def __init__(self):
        """
        Handle HTTP session related work.
        """
        super(OSFSession, self).__init__()
        self.base_url = 'https://api.osf.io/v2'

    def token_auth(self, token):
        """
        Add the user's OSF API token to the header for authorization.

        Parameters
        ----------
        token : str
            User's OSF token
        """
        self.headers.update({'Authorization': 'Bearer {}'.format(token)})

    def build_url(self, *args):
        """
        Takes in a list of arguments and uses them to build a
        url that gets appended to the base url.

        *args = ['me', 'nodes'] will build 'https://api.osf.io/v2/me/nodes/'
        """
        parts = [self.base_url]
        parts.extend(args)
        # canonical OSF URLs end with a slash
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

        response = super(OSFSession, self).get(url, *args, **kwargs)
        if response.status_code == 401:
            raise RuntimeError("Response returned with 401 status.")
        return response