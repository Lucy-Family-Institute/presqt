import requests


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

    def token_auth(self, header_dict):
        """
        Add the user's API token to the header for authorization.

        Parameters
        ----------
        header_dict : dict
            Dictionary containing what's expected for the partner endpoints
        """
        self.headers.update(header_dict)

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

    def build_urls(self, *args):
        parts = [self.base_url]
        return '/'.join(parts)
