from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_TEST_USER_TOKEN
from presqt.api_v1.utilities import get_action_message


class TestResourceCollection(SimpleTestCase):
    """
    Test the 'api_v1/targets/{target_name}/resources/' endpoint's GET method.
    Only checking PresQT Core code.

    Testing only PresQT core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}

    def test_get_error_400_missing_token(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})

    def test_get_error_400_target_not_supported_test_target(self):
        """
        Return a 400 if the GET method fails because the target requested does not support
        this endpoint's action.
        """
        with open('presqt/api_v1/tests/resources/targets_test.json') as json_file:
            with patch("builtins.open") as mock_file:
                mock_file.return_value = json_file
                url = reverse('resource_collection', kwargs={
                              'target_name': 'test'})
                response = self.client.get(url, **self.header)
                # Verify the error status code and message
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.data,
                    {'error': "PresQT Error: 'test' does not support the action 'resource_collection'."})

    def test_get_error_404_bad_target_name(self):
        """
        Return a 404 if the GET method fails because a bad target_name was given.
        """
        url = reverse('resource_collection', kwargs={
                      'target_name': 'bad_name'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "PresQT Error: 'bad_name' is not a valid Target name."})

    def test_action_message_with_fixity_and_metadata_errors(self):
        """
        If get_action_message is called and fixity and metadata has failed, we need to make the user
        aware.
        """
        error_message = get_action_message('Download', False, False, {
            "sourceTargetName": "egg", "destinationTargetName": "egg2"})

        self.assertEqual(error_message, 'Download successful but with fixity and metadata errors.')

    def test_write_and_validate_metadata_error(self):
        """
        If write and validate metadata call returns an error, we need to make the user aware.
        """
        self.destination_target_name = 'osf'
        self.destination_token = 'bad_token_eggs'
        from presqt.api_v1.utilities.metadata.upload_metadata import write_and_validate_metadata

        response = write_and_validate_metadata(self, 'nope', {'BAD': 'METADATA'})
        self.assertEqual(response.__str__(),
                         'Token is invalid. Response returned a 401 status code.')
