from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import CURATE_ND_TEST_TOKEN


class TestResourceCollection(TestCase):
    """
    Test the 'api_v1/targets/curate_nd/resources' endpoint's GET method.

    Testing Curate ND integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': CURATE_ND_TEST_TOKEN}

    def test_success_curate_nd(self):
        """
        Return a 200 if the GET method is successful when grabbing CurateND resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'curate_nd'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect,
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(28, len(response.data))
        for data in response.data:
            # Since Curate for now only supports details, there should only be one link for each object.
            self.assertEqual(len(data['links']), 1)

    def test_error_400_missing_token_curate_nd(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'curate_nd'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "'presqt-source-token' missing in the request headers."})

    def test_error_401_invalid_token_curate_nd(self):
        """
`       Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'eggyboi'}
        url = reverse('resource_collection', kwargs={'target_name': 'curate_nd'})
        response = client.get(url, **header)
        # Verify the error status code and message.
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})
