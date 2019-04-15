from presqt.osf.osf_classes.osf_core import OSFCore


class OSFFile(OSFCore):
    """
    Class that represents a File in the OSF API
    """
    def __init__(self, file_url, token):
        """
        Set the url and token attributes before the parent class __init__() gets called.

        Parameters
        ----------
        file_url: str
            URL to OSF API representing the file
        token: str
            User's OSF Token
        """
        # https://api.osf.io/v2/files/{file_id}/
        self.url = file_url
        self.token = token
        super(OSFFile, self).__init__()

    def update_attributes(self):
        """
        Add attributes to the class based on the JSON provided in the API call
        """
        file_data = self.json['data']
        self.id = self.get_attribute(file_data, 'id')
        self.title = self.get_attribute(file_data, 'attributes', 'name')
        self.download_link = self.get_attribute(file_data, 'links', 'download')
        self.sha256 = self.get_attribute(file_data, 'attributes', 'extra', 'hashes', 'sha256')
        self.md5 = self.get_attribute(file_data, 'attributes', 'extra', 'hashes', 'md5')

    def __str__(self):
        return '<File [{} - {}]>'.format(self.id, self.title)

    def get_object(self):
        return {
            'id': self.id,
            'title':self.title,
            'download_link': self.download_link,
            'sha256': self.sha256,
            'md5': self.md5,
            'url': self.url
        }