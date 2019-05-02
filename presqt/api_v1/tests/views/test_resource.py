from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient


class TestResourceCollection(TestCase):
    """
    Test the 'api_v1/target/{target_name}/resources/' endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {
            'HTTP_PRESQT_SOURCE_TOKEN':
                'iTa4pxa3DyPtT1sTlJ2Quy5q3ZhhHWNAmTmiTq2zI0XDxgjg4iWFSKPjRmQPk3BmrZhKGC'}

    def test_get_success_osf(self):
        """
        Return a 200 if the GET method is successful when grabbing OSF resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 200)

        keys = ['kind', 'kind_name', 'id', 'container', 'title']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

    def test_get_error_400_bad_target_name(self):
        """
        Return a 400 if the GET method fails because a bad target_name was given.

        """
        url = reverse('resource_collection', kwargs={'target_name': 'bad_name'})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})

    def test_get_error_400_missing_token(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "'presqt-source-token' missing in the request header."})

    def test_get_error_401_unauthorized(self):
        """
`       Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = client.get(url, **header)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "The Token provided is not authorized to access this asset."})