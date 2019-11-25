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
        response = self.client.get(reverse('target_collection'))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)

        # Verify that the first dictionary in the payload's array has the correct keys
        expected_keys = ['name', 'readable_name', 'supported_actions', 'supported_transfer_partners',
                         'supported_hash_algorithms', 'links']
        
        expected_supported_keys = ['resource_collection', 'resource_detail', 'resource_download',
                                   'resource_upload', 'resource_transfer_in', 'resource_transfer_out']
        for dict_item in response.data:
            self.assertListEqual(list(dict_item.keys()), expected_keys)
            self.assertListEqual(list(dict_item['supported_actions'].keys()),
                                 expected_supported_keys)

        json_data = read_file('presqt/targets.json', True)
        # Verify that the same amount of Target dictionaries exist in the payload and the original
        # json array
        self.assertEqual(len(json_data), len(response.data))


class TestTarget(SimpleTestCase):
    """
    Test the `api_v1/targets/{target_name}/` endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()

    def test_get_success(self):
        """
        Return a 200 if the GET method is successful
        """
        json_data = read_file('presqt/targets.json', True)

        for target in json_data:
            # Looping through targets and running tests on each one.
            target_name = target['name']
            # Making this variable so we can append detail to
            # the list in the test case.
            target_keys = list(target.keys())
            target_keys.append('links')

            url = reverse('target', kwargs={'target_name': target_name})
            response = self.client.get(url)

            # Verify the Status Code
            self.assertEqual(response.status_code, 200)
            # Verify that the payload keys are the same as the original target's json keys
            self.assertListEqual(list(response.data.keys()), target_keys)
            self.assertListEqual(list(response.data['supported_actions'].keys()),
                                 list(target['supported_actions'].keys()))

    def test_get_failure(self):
        """
        Return a 404 if an invalid target_name was provided in the URL
        """
        url = reverse('target', kwargs={'target_name': 'Failure!!!'})
        response = self.client.get(url)

        # Verify the Status Code
        self.assertEqual(response.status_code, 404)
