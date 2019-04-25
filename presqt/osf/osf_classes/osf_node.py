from presqt.osf.osf_classes.osf_core import OSFCore
from presqt.osf.osf_classes.osf_storage import OSFStorage


class OSFNode(OSFCore):
    """
    Class that represents a Node in the OSF API
    """
    def __init__(self, node_url, token):
        """
        Set the url and token attributes before the parent class __init__() gets called.

        Parameters
        ----------
        node_url: str
            URL to OSF API representing the node
        token: str
            User's OSF Token
        """
        # https://api.osf.io/v2/nodes/{node_id}/
        self.url = node_url
        self.token = token
        super(OSFNode, self).__init__()

    def update_attributes(self):
        """
        Add attributes to the class based on the JSON provided in the API call
        """
        project_data = self.json['data']
        self.id = project_data['id']
        self.title = project_data['attributes']['title']

        # If the node doesn't have a parent then the key "parent" won't exist in the JSON
        try:
            self.parent_id = project_data['relationships']['parent']['data']['id']
        except KeyError as e:
            # Check if the correct 'error' was raised otherwise it's an actual error.
            if e.args[0] == 'parent':
                self.parent_id = None
            else:
                raise

    def __str__(self):
        return '<Node [{} - {}]>'.format(self.id, self.title)

    @property
    def get_storages(self):
        """
        Get all storage providers for the given Node.

        Returns
        -------
        List of OSFStorage classes
        """

        storages_url = self.json['data']['relationships']['files']['links']['related']['href']
        # https://api.osf.io/v2/nodes/{node_id}/files/
        storages = self.get_request_json(storages_url, token=self.token)
        storage_list = []
        for store in storages['data']:
            provider_name = store['attributes']['name']
            storage_list.append(OSFStorage(storages_url + 'providers/{}/'.format(provider_name),
                                           token=self.token))
        return storage_list

    def get_object(self):
        return {
            'id': self.id,
            'title': self.title,
            'parent_id': self.parent_id,
            'url': self.url
        }