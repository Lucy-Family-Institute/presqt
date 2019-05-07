from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient


class TestResourceCollection(TestCase):
    """
    Test the 'api_v1/targets/{target_name}/resources/' endpoint's GET method.
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

        keys = ['kind', 'kind_name', 'id', 'container']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

    def test_get_error_404_bad_target_name(self):
        """
        Return a 404 if the GET method fails because a bad target_name was given.

        """
        url = reverse('resource_collection', kwargs={'target_name': 'bad_name'})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})

    def test_get_error_401_missing_token(self):
        """
        Return a 401 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "'presqt-source-token' missing in the request headers."})


class TestResource(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}/` endpoint's GET method.
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
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': '3'})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 200)

        keys = ['id', 'title']
        self.assertListEqual(keys, list(response.data.keys()))

    def test_get_error_404_bad_target_name(self):
        """
        Return a 404 if the GET method fails because a bad target_name was given.

        """
        url = reverse('resource', kwargs={'target_name': 'bad_name', 'resource_id': '3'})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})

    def test_get_error_401_missing_token(self):
        """
        Return a 401 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': '3'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "'presqt-source-token' missing in the request headers."})