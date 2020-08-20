from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_TEST_USER_TOKEN
from presqt.api_v1.utilities import hash_tokens


class TestCollectionJobGET(SimpleTestCase):
    """
    Test the `api_v1/job_status/collection/` endpoint's GET method.

    Testing only PresQT core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.target_name = 'osf'
        self.ticket_number = hash_tokens(OSF_TEST_USER_TOKEN)

    def test_success(self):
        collection_url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        collection_response = self.client.get(collection_url,  **self.header)

        # Verify the status code
        self.assertEqual(collection_response.status_code, 200)

        collection_status_url = reverse('job_status', kwargs={'action': 'collection'})
        collection_status_response = self.client.get(collection_status_url, **self.header)

        # Verify the status code
        self.assertEqual(collection_status_response.status_code, 200)
        self.assertEqual(collection_status_response.data['job_percentage'], 99)
        self.assertEqual(collection_status_response.data['status'], 'finished')

    def test_error_bad_token(self):
        headers = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}

        collection_url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        collection_response = self.client.get(collection_url, **headers)
        self.assertEqual(collection_response.status_code, 401)


        collection_status_url = reverse('job_status', kwargs={'action': 'collection'})
        collection_status_response = self.client.get(collection_status_url, **headers)

        self.assertEqual(collection_status_response.status_code, 400)
        self.assertEqual(collection_status_response.data['error'], 'PresQT Error: Bad token provided')

    def test_error_token_missing(self):
        headers = {}
        collection_status_url = reverse('job_status', kwargs={'action': 'collection'})
        collection_status_response = self.client.get(collection_status_url, **headers)

        self.assertEqual(collection_status_response.status_code, 400)
        self.assertEqual(collection_status_response.data['error'], "PresQT Error: 'presqt-source-token' missing in the request headers.")

    def test_bad_action(self):
        collection_status_url = reverse('job_status', kwargs={'action': 'bad_action'})
        collection_status_response = self.client.get(collection_status_url, **self.header)

        self.assertEqual(collection_status_response.status_code, 400)
        self.assertEqual(collection_status_response.data['error'], "PresQT Error: 'bad_action' is not a valid acton.")



