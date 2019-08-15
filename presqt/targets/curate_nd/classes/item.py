from presqt.targets.curate_nd.classes.base import CurateNDBase


class Item(CurateNDBase):
    """
    Class that represents an item in the Curate ND API.
    """

    def __init__(self, item, session):
        super(Item, self).__init__(item, session)

        # Add attributes to the class based on the JSON provided in the API call.
        self.id = item['id']
        # Links
        self.endpoint = item['']
