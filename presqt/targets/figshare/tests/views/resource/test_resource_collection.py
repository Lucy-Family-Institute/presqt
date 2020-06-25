import requests
from django.test import SimpleTestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from config.settings.base import FIGSHARE_TEST_USER_TOKEN


class TestResourceCollection(SimpleTestCase):
    """
    Test the 'api_v1/targets/figshare/resources' endpoint's GET method.

    Testing Figshare integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': FIGSHARE_TEST_USER_TOKEN}

    def test_success_figshare(self):
        """
        Return a 200 if the GET method is successful when grabbing FigShare resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'figshare'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(len(response.data), 3)

        for data in response.data:
            self.assertEqual(len(data['links']), 1)

    def test_success_with_search(self):
        """
        Return a 200 if the GET method was successfull with search parameters.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'figshare'})
        response = self.client.get(url + '?id=82430', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(len(response.data), 7)
        for data in response.data:
            self.assertEqual(len(data['links']), 1)

    def test_404_no_search_results(self):
        """
        Return a 404 if no search results were found.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'figshare'})
        response = self.client.get(url + '?id=egg', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], "Project with id, egg, can not be found.")

    def test_error_400_missing_token_figshare(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'figshare'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})

    def test_error_401_invalid_token_figshare(self):
        """
        Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'eggyboi'}
        url = reverse('resource_collection', kwargs={'target_name': 'figshare'})
        response = client.get(url, **header)
        # Verify the error status code and message.
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

    def test_error_400_bad_search_parameters(self):
        """
        Test for a 400 with a bad parameter
        """
        url = reverse('resource_collection', kwargs={'target_name': 'figshare'})
        response = self.client.get(url + '?title=hat', **self.header)

        self.assertEqual(
            response.data['error'], 'PresQT Error: FigShare does not support title as a search parameter.')
        self.assertEqual(response.status_code, 400)
