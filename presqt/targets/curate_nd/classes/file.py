from rest_framework import status

from presqt.targets.curate_nd.classes.base import CurateNDBase
from presqt.utilities import PresQTResponseException


class File(CurateNDBase):
    """
    Class that represents a File in the CurateND API.
    """
    def __init__(self, file, session):
        super(File, self).__init__(file, session)

        # Add attributes to the class based on the JSON provided in the API call.
        self.id = file['id']
        # Links
        self.endpoint = file['requestUrl']
        self.download_url = file['downloadUrl']
        self.thumbnail_url = file['thumnailUrl']

        # Attributes
        self.kind = 'item'
        self.kind_name = 'file'
        self.title = file['title']
        self.date_submitted = file['dateSubmitted']
        self.modified_date = file['modified']
        self.creator = file['creator']
        self.depositor = file['depositor']
        self.has_model = file['hasModel']
        self.is_part_of = file['isPartOf']
        self.characterization = file['characterization']

        # Extra
        self.hashes = []
        self.md5 = None
        self.sha256 = None

    def download(self):
        """
        Download the file using the download url.

        Returns
        -------
        The requesed file in byte format.
        """
        response = self.get(self.download_url)
        return response.content
