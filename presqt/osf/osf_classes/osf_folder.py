from presqt.osf.osf_classes.osf_core import OSFCore, ContainerMixin


class OSFFolder(OSFCore, ContainerMixin):
    """
    Class that represents a Folder in the OSF API
    """
    def __init__(self, folder_url, token):
        """
        Set the url and token attributes before the parent class __init__() gets called.

        Parameters
        ----------
        folder_url: str
            URL to OSF API representing the folder
        token: str
            User's OSF Token
        """
        # https://api.osf.io/v2/files/{file_id}/
        self.url = folder_url
        self.token = token
        super(OSFFolder, self).__init__()

    def update_attributes(self):
        """
        Add attributes to the class based on the JSON provided in the API call
        """
        folder_data = self.json['data']
        self.id = folder_data['id']
        self.title = folder_data['attributes']['name']

    def __str__(self):
        return '<Folder [{} - {}]>'.format(self.id, self.title)

    def get_object(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url
        }