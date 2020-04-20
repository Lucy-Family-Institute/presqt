import json

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from presqt.utilities import read_file


class TestTargetCollection(SimpleTestCase):
    """
    Test the `api_v1/targets/` endpoint's GET method.
    """

    def test_get_success(self):
        """
        Return a 200 if the GET method is successful
        """
        response = self.client.get(reverse('status_collection'))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        print(json.dumps(response.data, indent=2))
