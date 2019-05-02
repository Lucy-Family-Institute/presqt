from presqt.osf.osf_classes.osf_session import OSFSession

class OSFCore(object):
    """
    Base class for all OSF classes and the main OSF object.
    """
    def __init__(self, json, session=None):
        # Set the session attribute with the existing session or a new one if one doesn't exist.
        if session is None:
            self.session = OSFSession()
        else:
            self.session = session

        # Set the class attributes
        self._update_attributes(json)

    def _update_attributes(self, json):
        """
        Empty method expected to be overwritten in the subclass to add individual attributes
        to the class.
        """
        pass

    def _build_url(self, *args):
        """
        Takes in a list of arguments and uses them to build a
        url that gets appended to the base url.

        *args = ['me', 'nodes'] will build 'https://api.osf.io/v2/me/nodes/'
        """
        return self.session.build_url(*args)

    def _get(self, url, *args, **kwargs):
        """
        Performs a get request based on the base session get method.
        """
        return self.session.get(url, *args, **kwargs)

    def _json(self, response):
        """
        Extract JSON from response if `status_code` is 200.
        """
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError("Response has status code {} not 200".format(response.status_code))

    def _follow_next(self, url):
        """
        Follow the 'next' link on paginated results.
        """
        response_json = self._json(self._get(url))
        data = response_json['data']

        next_url = response_json['links']['next']
        while next_url is not None:
            response_json = self._json(self._get(next_url))
            data.extend(response_json['data'])
            next_url = response_json['links']['next']

        return data
