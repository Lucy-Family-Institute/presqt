from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_PRESQT_FORK_TOKEN, OSF_TEST_USER_TOKEN, OSF_PRIVATE_USER_TOKEN


class TestResourceCollection(SimpleTestCase):
    """
    Test the 'api_v1/targets/osf/resources/' endpoint's GET method.

    Testing OSF integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.large_project_header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_PRESQT_FORK_TOKEN}

    def test_success(self):
        """
        Return a 200 if the GET method is successful when grabbing OSF resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(75, len(response.data))
        for data in response.data:
            self.assertEqual(len(data['links']), 1)

    def test_success_with_search(self):
        """
        Return a 200 if the GET method is successful when grabbing OSF resources with a search query.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.get(url+'?title=hcv+and+nhl+risk', **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

        # Ensure we are only get back the first page of results
        response = self.client.get(url + '?title=egg', **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

        ### Search by ID ###
        response = self.client.get(url+'?id=zxbhs', **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

        # Search By Author
        response = self.client.get(url+'?author=Prometheus', **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

        # Search by Keywords
        response = self.client.get(url + "?keywords=egg", **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

    def test_success_large_project(self):
        """
        Return a 200 if the GET method is successful when grabbing OSF resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.get(url, **self.large_project_header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(119, len(response.data))

    def test_error_401_invalid_token(self):
        """
`       Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = client.get(url, **header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

    def test_error_400_bad_search_parameters(self):
        """
        If a bad search request is made, we want to make the user aware.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        # TOO MANY KEYS
        response = self.client.get(url + '?title=hat&spaghetti=egg', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: The search query is not formatted correctly.')
        self.assertEqual(response.status_code, 400)

        # BAD KEY
        response = self.client.get(url + '?spaghetti=egg', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: OSF does not support spaghetti as a search parameter.')
        self.assertEqual(response.status_code, 400)

        # SPECIAL CHARACTERS IN THE REQUEST
        response = self.client.get(url + '?title=egg:boi', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: The search query is not formatted correctly.')
        self.assertEqual(response.status_code, 400)

        # EMPTY SEARCH -- NOT AN ERROR
        response = self.client.get(url + '?title=', **self.header)
        # Should return users resources
        self.assertEqual(response.status_code, 200)
        # Verify the count of resource objects is what we expect.
        self.assertEqual(75, len(response.data))
