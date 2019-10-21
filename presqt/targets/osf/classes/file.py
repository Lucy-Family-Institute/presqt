from presqt.targets.osf.classes.base import OSFBase


class File(OSFBase):
    """
    Class that represents a File in the OSF API.
    """
    def __init__(self, file, session):
        super(File, self).__init__(file, session)

        # Add attributes to the class based on the JSON provided in the API call.
        self.id = file['id']

        related = file['relationships']['target']['links']['related']
        if related['meta']['type'] == 'node':
            self.parent_project_id = related['href'][-6:-1]
        # Links
        self.endpoint = file['links']['self']
        self.download_url = file['links']['move']
        self.upload_url = file['links']['upload']
        self.delete_url = file['links']['delete']

        # Attributes
        attrs = file['attributes']
        self.kind = 'item'
        self.kind_name = 'file'
        self.title = attrs['name']
        self.last_touched = attrs['last_touched']
        self.materialized_path = attrs['materialized_path']
        self.date_modified = attrs['date_modified']
        self.current_version = attrs['current_version']
        self.date_created = attrs['date_created']
        self.provider = attrs['provider']
        self.path = attrs['path']
        self.current_user_can_comment = attrs['current_user_can_comment']
        self.guid = attrs['guid']
        self.checkout = attrs['checkout']
        self.tags = attrs['tags']
        self.size = attrs['size']
        # Extra
        extra = attrs['extra']
        self.hashes = extra['hashes']
        self.sha256 = extra['hashes']['sha256']
        self.md5 = extra['hashes']['md5']

    def download(self):
        """
        Download the file using the download_url.

        Returns
        -------
        The requested file in byte format.
        """
        response = self.get(self.download_url)
        return response.content

    def update(self, file_to_write):
        """
        Update the file with a new file

        Parameters
        ----------
        file_to_write : binary_file
            File contents to update the file with.

        Returns
        -------
        HTTP Rsponse object
        """

        response = self.put(self.upload_url, data=file_to_write)
        return response
