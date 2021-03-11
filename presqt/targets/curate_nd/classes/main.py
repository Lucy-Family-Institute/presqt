import requests

from rest_framework import status

from presqt.targets.curate_nd.classes.base import CurateNDBase
from presqt.targets.curate_nd.classes.file import File
from presqt.targets.curate_nd.classes.item import Item
from presqt.targets.utilities import run_urls_async
from presqt.utilities import (PresQTInvalidTokenError, PresQTResponseException, update_process_info,
                              increment_process_info)


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
        response = requests.get('https://curate.nd.edu/api/items?editor=self',
                                headers={'X-Api-Token': '{}'.format(token)})
        try:
            response.json()['error']
        except KeyError:
            pass
        else:
            raise PresQTInvalidTokenError("Token is invalid. Response returned a 500 error.")

    def items(self, url):
        """
        Get all items.

        Parameters
        ----------
        url : str
            The url used to retrive all items.

        Returns
        -------
        List of the desired Items.
        """
        response_data = self._get_all_paginated_data(url)
        item_urls = []
        for response in response_data:
            if response['type'] == 'Person':
                pass
            else:
                item_urls.append(response['itemUrl'])

        data = run_urls_async(self, item_urls)

        # Remove errors returned by CurateND
        good_data = []
        for item in data:
            if item:
                try:
                    item['status']
                except KeyError:
                    good_data.append(item)
                else:
                    pass

        return [Item(item_json, self.session) for item_json in good_data]

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
        # If the id given can't be found or is of type person, we want to raise an exception.
        # Error are only present in the payload if an error occured.
        if 'error' in response_json.keys():
            raise PresQTResponseException(
                'The resource, {}, could not be found on CurateND.'.format(resource_id),
                status.HTTP_404_NOT_FOUND)

        try:
            response_json['containedFiles']
        except KeyError:
            # If the containedFiles key is not in the payload, we are creating a file.
            return File(response_data.json(), self.session)
        else:
            return Item(response_data.json(), self.session)

    def get_resources(self, url=None):
        """
        Get all of the requested resources. Return in the structure expected for the PresQT API.

        Parameters
        ----------
        process_info_path: str
            Path to the process info file that keeps track of the action's progress
        url : str
            The url used to retrive all items.

        Returns
        -------
        List of all items.
        """
        resources = []
        items = self.items(url)

        for item in items:
            # Items
            resources.append({
                'kind': 'container',
                'kind_name': 'item',
                'id': item.id,
                'container': None,
                'title': item.title})

        return resources
