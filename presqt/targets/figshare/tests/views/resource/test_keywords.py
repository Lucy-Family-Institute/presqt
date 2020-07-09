
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import FIGSHARE_TEST_USER_TOKEN


class TestResourceKeywords(SimpleTestCase):
    """
    Test the `api_v1/targets/figshare/resources/{resource_id}/keywords/` endpoint's GET method.

    Testing FigShare integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': FIGSHARE_TEST_USER_TOKEN}
        self.keys = ['keywords', 'enhanced_keywords', 'all_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting a GitLab `project`.
        """
        resource_id = '83375:12533801'
        url = reverse('keywords', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Spot check some individual keywords
        self.assertIn('ecoute', response.data['keywords'])
        self.assertIn('listen', response.data['keywords'])
        self.assertIn('ear', response.data['keywords'])

    def test_error_project_keywords(self):
        """
        Returns a 400 if the GET method is unsuccessful when getting a FigShare `file` keywords.
        """
        resource_id = "83375:12533801:23301149"
        url = reverse('keywords', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "FigShare projects/files do no have keywords.")
    
    def test_bad_token(self):
        """
        Returns a 401 if token is invalid.
        """
        resource_id = "83375:12533801:23301149"
        url = reverse('keywords', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id})
        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': "BAD"})
        # Verify the status code
        self.assertEqual(response.status_code, 401)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "Token is invalid. Response returned a 401 status code.")
