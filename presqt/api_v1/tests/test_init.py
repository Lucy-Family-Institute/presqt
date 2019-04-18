from django.test import TestCase, Client
from rest_framework.reverse import reverse


class TestApiRoot(TestCase):
    """
    Test the endpoint `api_v1/`
    """
    def test_success(self):
        """
        Return a 200 if successful
        """
        client = Client()
        response = client.get(reverse('api_root'))
        self.assertEqual(response.status_code, 200)