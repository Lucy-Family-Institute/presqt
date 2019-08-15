import json
import requests

from rest_framework import status

from presqt.targets.curate_nd.classes.base import CurateNDBase
from presqt.utilities import (PresQTResponseException, PresQTInvalidTokenError,
                              get_dictionary_from_list)


class CurateND(CurateNDBase):
    """
    Interact with Curate ND.
    This is the main poinmt of contact for ineractions with CurateND.
    Use the methods of this class to find projects, login to CurateND, etc.
    """

    def __init__(self, token):
        super(CurateND, self).__init__({})
        self.login(token)

    def login(self, token):
        """
        Login user for API calls.

        Parameters
        ----------
        token : str
            Token of the user performing the request.
        """
        self.session.token_auth({'X-Api-Token': '{}'.format(token)})
        # Verify that the token provided is a valid one.
        response = requests.get('https://libvirt6.library.nd.edu/api/items?editor=self',
                                headers={'X-Api-Token': '{}'.format(token)})
        if response.status_code == 500:
            raise PresQTInvalidTokenError(
                "Token is invalid. Response returned a 500 error.")

    def item(self, item_id):
        """
        Get an item with the given item_id.

        Parameters
        ----------
        item_id : str
            id of the Item we want to fetch.

        Returns
        -------
        Instance of the desired Item.
        """
        url = self.session.build_url(item_id)
