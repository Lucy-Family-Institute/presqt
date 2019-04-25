import requests


class OSFCore(object):
    """
    Base class for all OSF classes.

    'json' will get assigned in the __init__
    'url' and 'token' will get assigned in the subclass __init__ before they are used here
    """
    json = None
    url = None
    token = None

    def __init__(self):
        # Get the response JSON from an OSF API call provided by the subclass
        self.json = self.get_request_json(self.url, self.token)

        # Add attributes to the class from the JSON gathered from the response
        self.update_attributes()

    def get_request_json(self, url, token):
        """
        Make a GET request to the provided URL with the provided token

        Parameters
        ----------
        url : str
            URL string for the request
        token : str
            User's OSF Token

        Returns
        -------
        JSON decoded response
        """
        headers = {'Authorization': 'Bearer {}'.format(token)}
        response = requests.get(url, headers=headers)
        return response.json()

    def update_attributes(self):
        """
        Empty method expected to be overwritten in the subclass to add individual attributes
        to the class.
        """
        pass

    def get_attribute(self, json, *keys):
        """
        Get a value out of a nested dictionary/JSON.

        Parameters
        ----------
        json : dict
            The json dict we want to traverse

        keys : list
            The list of keys that will make up the dict traversal

        Returns
        -------
        Value found in the nested dictionary/json
        """
        value = json
        for key in keys:
            value = value[key]
        return value

    def follow_next(self, url):
        """
        For provider/folder endpoints that have data lists, follow the
        'next' link on paginated results.

        It effectively constructs a 'data' obj based on all of the paginated data sets.

        Parameters
        ----------
        url: str
            URL to the provider/folder endpoint that has paginated data to be traversed

        Returns
        -------
        Obj that holds all of the paginated data
        """
        # https://api.osf.io/v2/nodes/{node_id}/files/{provider}/
        # https://api.osf.io/v2/nodes/{node_id}/files/{provider}/{path}
        response_json = self.get_request_json(url, self.token)

        data = response_json['data']
        next_url = self.get_attribute(response_json, 'links', 'next')
        while next_url is not None:
            response = (self.get_request_json(next_url, self.token))
            data.extend(response['data'])
            next_url = self.get_attribute(response, 'links', 'next')

        return data


class ContainerMixin:
    """
    Mixin class for OSF classes that need to traverse containers (project/folder)
    to create a list of all assets while maintaining their hierarchy.
    """
    file_keys = ('relationships', 'files', 'links', 'related', 'href')

    def get_assets_objects(self, file_klass, folder_klass, container):
        """
        For the container get all folders/files within it. Create and send back objects for each
        asset. We create the objects here so we can keep track of parent containers for each asset.

        The general idea is to yield all files within the highest level of the container first.
        Then traverse each subcontainer. For each subcontainer do the exact same process.

        Parameters
        ----------
        file_klass: OSFFile class instance
            In instance of an OSFFile. This has to be passed as a parameter for import reasons.

        folder_klass : OSFFolder class instance
            In instance of an OSFFolder. This has to be passed as a parameter for import reasons.

        container : str
            Parent container UUID.

        Returns
        -------
        List of file and folder objects.

        """
        asset_list = []
        children = self.follow_next(self.get_attribute(self.json['data'], *self.file_keys))
        while children:
            child = children.pop()
            kind = child['attributes']['kind']
            if kind == 'file':
                file_object = file_klass(self.get_attribute(child, 'links', 'self'), self.token)
                asset_list.append({
                    'kind': 'item',
                    'kind_name': 'file',
                    'id': file_object.id,
                    'container': container,
                })
            else:
                folder_object = folder_klass(self.get_attribute(child, 'links', 'self'), self.token)
                asset_list.append({
                    'kind': 'container',
                    'kind_name': 'folder',
                    'id': folder_object.id,
                    'container': container,
                })
                for folder in folder_object.get_assets_objects(file_klass, folder_klass, folder_object.id):
                    asset_list.append(folder)
        return asset_list