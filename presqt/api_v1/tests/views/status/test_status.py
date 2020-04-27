from unittest.mock import patch

import requests
from django.test import SimpleTestCase
from rest_framework.reverse import reverse

from presqt.utilities import read_file


class TestTargetCollection(SimpleTestCase):
    """
    Test the `api_v1/statuses/` endpoint's GET method.
    """

    targets = read_file("presqt/specs/targets.json", True)

    def test_get_success(self):
        """
        Return a 200 if the GET method is successful
        """
        response = self.client.get(reverse("status_collection"))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), len(self.targets))

        item: dict
        for item in response.data:
            self.assertIn("service", item.keys())
            self.assertIn("status", item.keys())
            self.assertIn("detail", item.keys())

    def test_get_error(self):
        """
        Return status "timeout" if all connections timeout
        """
        with patch.object(
            requests.Response, "raise_for_status", side_effect=requests.ConnectTimeout()
        ) as mock_method:
            response = self.client.get(reverse("status_collection"))
            # Verify the Status Code
            self.assertEqual(response.status_code, 200)

            self.assertEqual(len(response.data), len(self.targets))

            item: dict
            for item in response.data:
                self.assertIn("service", item.keys())
                self.assertIn("status", item.keys())
                self.assertIn("detail", item.keys())
                self.assertEqual(item["status"], "timeout")
