from presqt.osf.classes.base import OSFBase


class File(OSFBase):
    """
    Class that represents a File in the OSF API.
    """
    def _populate_attributes(self, file):
        """
        Add attributes to the class based on the JSON provided in the API call.

        Parameters
        ----------
        file : dict
            Data dictionary returned from the json response to create the File class instance.
        """
        if not file:
            return

        self.id = file['id']
        self._endpoint = file['links']['self']
        self._download_url = file['links']['download']
        self._upload_url = file['links']['upload']
        self._delete_url = file['links']['delete']
        self.osf_path = file['attributes']['path']
        self.path = file['attributes']['materialized_path']
        self.name = file['attributes']['name']
        self.date_created = file['attributes']['date_created']
        self.date_modified = file['attributes']['date_modified']
        self.hashes = file['attributes']['extra']['hashes']

    def __str__(self):
        return '<File [{}, {}]>'.format(self.id, self.path)