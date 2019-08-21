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
        self.creator = item['creator']
        self.created = item['created']
        self.creator_administrative_unit = item['creator#administrative_unit']
        self.rights = item['rights']
        self.modified = item['modified']
        self.access = item['access']
        self.depositor = item['depositor']
        self.owner = item['owner']
        self.has_model = item['hasModel']
        self.representative = item['representative']
        self.contained_files = item['containedFiles']
        self.size = None
        self.sha256 = None
        self.md5 = None

        def get_all_files(self):           
            files = [file for file in self.contained_files]
            return files