import json
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

        # Attributes
        self.kind = 'item'
        self.kind_name = 'file'
        self.title = file['label']
        self.date_submitted = file['dateSubmitted']
        self.modified = file['modified']
        self.size = 0
        self.md5 = None
        self.sha256 = None
        self.extra = {}

        # Curate's API has inconsistent payloads, to get around a bunch of try/excepts, we will just
        # add these unknown fields to the extra...
        for key, value in file.items():
            if key not in ['id', 'requestUrl', 'downloadUrl', 'label', 'dateSubmitted', 'modified']:
                try:
                    self.extra[key].append(value)
                except KeyError:
                    self.extra[key] = value

    def download(self):
        """
        Download the file using the download url.

        Returns
        -------
        The requesed file in byte format.
        """
        response = self.get(self.download_url)
        return response.content
