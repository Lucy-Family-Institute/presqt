from presqt.targets.curate_nd.classes.base import CurateNDBase


class Item(CurateNDBase):
    """
    Class that represents an item in the Curate ND API.
    """

    def __init__(self, item, session):
        super(Item, self).__init__(item, session)

        # Add attributes to the class based on the JSON provided in the API call
        self.id = item['id']
        # Links
        self.endpoint = item['requestUrl']

        # Attributes
        self.kind = 'container'
        self.kind_name = 'item'
        self.title = item['title']
        self.date_submitted = item['dateSubmitted']
        self.modified = item['modified']
        self.size = None
        self.sha256 = None
        self.md5 = None
        self.extra = {}

        # Curate's API has inconsistent payloads, to get around a bunch of try/excepts, we will just
        # add these unknown fields to the extra...
        for key, value in item.items():
            if key not in ['id', 'requestUrl', 'downloadUrl', 'label', 'dateSubmitted', 'modified']:
                try:
                    self.extra[key].append(value)
                except KeyError:
                    self.extra[key] = value

        def get_all_files(self):
            files = [file for file in self.contained_files]
            return files
