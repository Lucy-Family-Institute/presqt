import json

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from presqt.api_v1.views.target import TargetsList, TargetDetails


class TestTargetsList(TestCase):
    """
    Test the `api_v1/targets/` endpoint's GET method.
    """
    def test_get_success(self):
        """
        Return a 200 if the GET method is successful
        """
        self.factory = APIRequestFactory()
        view = TargetsList.as_view()
        request = self.factory.get('api_v1/targets/')
        response = view(request)

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify that the first dictionary in the payload's array has the correct keys
        self.assertListEqual(list(response.data[0].keys()), ['name', 'read', 'write', 'detail'])

        with open('presqt/targets.json') as json_file:
            json_data = json.load(json_file)
        # Verify that the same amount of Target dictionaries exist in the payload and the original
        # json array
        self.assertEqual(len(json_data), len(response.data))


class TestTargetDetails(TestCase):
    """
    Test the `api_v1/target/{target_name}/` endpoint's GET method.
    """
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = TargetDetails.as_view()

    def test_get_success(self):
        """
        Return a 200 if the GET method is successful
        """
        with open('presqt/targets.json') as json_file:
            json_data = json.load(json_file)
        target_name = json_data[0]['name']

        request = self.factory.get('/target/{}'.format(target_name))
        response = self.view(request, target_name)

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify that the payload keys are the same as the original target's json keys
        self.assertListEqual(list(response.data.keys()), list(json_data[0].keys()))

    def test_get_failure(self):
        """
        Return a 400 if an invalid target_name was provided in the URL
        """
        request = self.factory.get('/target/{}'.format('Failure!!!'))
        response = self.view(request, 'Failure!!!')
        # Verify the Status Code
        self.assertEqual(response.status_code, 400)