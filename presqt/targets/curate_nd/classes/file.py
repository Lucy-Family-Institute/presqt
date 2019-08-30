from rest_framework import status

from presqt.targets.curate_nd.classes.base import CurateNDBase


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
        self.md5 = None
        self.sha256 = None
        self.extra = {}

        # Curate's API has inconsistent payloads, to get around a bunch of try/excepts, we will just
        # add these unknown fields to the extra...
        for key, value in file.items():
            if key not in ['id', 'requestUrl', 'downloadUrl', 'label', 'dateSubmitted', 'modified']:
                self.extra[key] = value

        # Pulling the md5 checksum out of the payload
        try:
            md5_end = '</md5checksum>'
            md5_hash_check = self.extra['characterization'].partition(md5_end)[0]
            # Md5 hashes are 32 characters...
            self.md5 = md5_hash_check[len(md5_hash_check)-32:]
        except KeyError:  # pragma: no cover
            self.md5 = None

    def download(self):
        """
        Download the file using the download url.
    ​
        Returns
        -------
        The requested file in byte format and the file hash.
        """
        response = self.get(self.download_url)
        return response.content, response.headers['Content-Md5']