from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from presqt.api_v1 import api_root


class TestApiRoot(SimpleTestCase):
    """
    Test the endpoint `api_v1/`
    """
    def test_success(self):
        """
        Return a 200 if successful
        """
        self.factory = APIRequestFactory()
        view = api_root
        request = self.factory.get('api_root')
        response = view(request)
        self.assertEqual(response.status_code, 200)