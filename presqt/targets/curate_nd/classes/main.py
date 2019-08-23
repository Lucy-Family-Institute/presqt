import json
import requests

from rest_framework import status

from presqt.targets.curate_nd.classes.base import CurateNDBase
from presqt.targets.curate_nd.classes.item import Item
from presqt.utilities import (PresQTResponseException, PresQTInvalidTokenError,
                              get_dictionary_from_list)
from presqt.utilities import write_file


class CurateND(CurateNDBase):
    """
    Interact with Curate ND.
    This is the main point of contact for ineractions with CurateND.
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

    def items(self):
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
        url = self.session.build_urls()
        response_data = self._follow_next(url)
        item_urls = []
        for response in response_data:
            if response['type'] == 'Person':
                pass
            else:
                item_urls.append(response['itemUrl'])

        data = self.run_urls_async(item_urls)

        return [Item(item_json, self.session) for item_json in data]

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
        print('Im in!')
        url = self.session.build_url(item_id)
        response_data = self.get(url)
        print(response_data.json())

        return Item(response_data.json(), self.session)

    def get_user_items(self):
        """
        Get all of the user's items. Return in the structure expected for the PresQT API.

        Returns
        -------
        List of all items.
        """
        resources = []
        for item in self.items():
            resources.append({
                'kind': 'container',
                'kind_name': 'item',
                'id': item.id,
                'container': None,
                'title': item.title})

        return resources
