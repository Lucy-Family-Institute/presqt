from presqt.osf.osf_classes.osf_core import OSFCore, ContainerMixin


class OSFStorage(OSFCore, ContainerMixin):
    """
    Class that represents a Folder in the OSF API
    """
    def __init__(self, storage_url, token):
        """
        Set the url and token attributes before the parent class __init__() gets called.

        Parameters
        ----------
        storage_url: str
            URL to OSF API representing the storage
        token: str
            User's OSF Token
        """
        # https://api.osf.io/v2/nodes/{node_id}/files/providers/{provider}/
        self.url = storage_url
        self.token = token
        super(OSFStorage, self).__init__()

    def update_attributes(self):
        """
        Add attributes to the class based on the JSON provided in the API call
        """
        storage_data = self.json['data']
        self.id = storage_data['id']
        self.title = storage_data['attributes']['name']
        self.files_url = storage_data['relationships']['files']['links']['related']['href']

    def __str__(self):
        return '<Storage [{} - {}]>'.format(self.id, self.title)