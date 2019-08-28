import requests

from rest_framework import status

from presqt.targets.curate_nd.classes.base import CurateNDBase
from presqt.targets.curate_nd.classes.file import File
from presqt.targets.curate_nd.classes.item import Item
from presqt.utilities import PresQTInvalidTokenError


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
            raise PresQTInvalidTokenError("Token is invalid. Response returned a 500 error.")

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
        url = 'https://libvirt6.library.nd.edu/api/items?editor=self'
        response_data = self._get_all_paginated_data(url)
        item_urls = []
        for response in response_data:
            if response['type'] == 'Person':
                pass
            else:
                item_urls.append(response['itemUrl'])

        data = self.run_urls_async(item_urls)

        return [Item(item_json, self.session) for item_json in data]

    def resource(self, resource_id):
        """
        Get an item or file with the given resource_id.

        Parameters
        ----------
        resource_id : str
            id of the resource we want to fetch.

        Returns
        -------
        Instance of the desired resource.
        """
        url = self.session.build_url(resource_id)
        response_data = self.get(url)
        response_json = response_data.json()

        try:
            contained_files = response_json['containedFiles']
        except KeyError:
            # If the containedFiles key is not in the payload, we are creating a file.
            return File(response_data.json(), self.session)
        else:
            return Item(response_data.json(), self.session)

    def get_user_resources(self):
        """
        Get all of the user's resources. Return in the structure expected for the PresQT API.

        Returns
        -------
        List of all items.
        """
        resources = []
        for item in self.items():
            # Items
            resources.append({
                'kind': 'container',
                'kind_name': 'item',
                'id': item.id,
                'container': None,
                'title': item.title})
            # Files
            for file in item.extra['containedFiles']:
                container_id = file['isPartOf'][len(self.session.base_url)+1:]
                resources.append({
                    'kind': 'item',
                    'kind_name': 'file',
                    'id': file['id'],
                    'container': container_id,
                    'title': file['label']})

        return resources
