from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import TEST_USER_TOKEN


class TestResourceCollection(TestCase):
    """
    Test the 'api_v1/targets/{target_name}/resources/' endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}

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

        self.assertEqual(70, len(response.data))

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

    def test_get_error_401_invalid_token(self):
        """
`       Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = client.get(url, **header)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

class TestResource(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}/` endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}


    def test_get_success_osf_project(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a project.
        """
        resource_id = 'cmn5z'

        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 200)

        keys = ['id', 'title']
        self.assertListEqual(keys, list(response.data.keys()))
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('Test Project', response.data['title'])

    def test_get_success_osf_file(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a file.
        """
        resource_id = '5cd9831c054f5b001a5ca2af'

        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 200)

        keys = ['id', 'title']
        self.assertListEqual(keys, list(response.data.keys()))
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('2017-01-27 PresQT Workshop Planning Meeting Items.docx',
                         response.data['title'])

    def test_get_success_osf_folder(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a folder.
        """
        resource_id = '5cd9895b840cae001a708c31'
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 200)

        keys = ['id', 'title']
        self.assertListEqual(keys, list(response.data.keys()))
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('Docs', response.data['title'])

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

    def test_get_error_404_file_id_doesnt_exist(self):
        """
        Return a 404 if the GET method fails because the file_id given does not map to a resource.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': '1234'})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data,
                         {'error': "Resource with id '1234' not found for this user."})

    def test_get_error_403_not_authorized(self):
        """
        Return a 403 if the GET method fails because the user doesn't have access to this resource.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'q5xmw'})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data,
            {'error': "User does not have access to this resource with the token provided."})