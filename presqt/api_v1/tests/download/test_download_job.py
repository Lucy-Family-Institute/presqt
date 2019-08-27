import io
import json
import shutil
import zipfile

from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_TEST_USER_TOKEN
from presqt.utilities import write_file, read_file
from presqt.targets.utilities import call_get_resource_zip
from presqt.api_v1.utilities.fixity.download_fixity_checker import download_fixity_checker


class TestDownloadJob(TestCase):
    """
    Test the `api_v1/downloads/<ticket_id>/` endpoint's GET method.

    Testing OSF Integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.resource_id = '5cd98510f244ec001fe5632f'
        self.target_name = 'osf'

    def test_error_400(self):
        """
        Return a 400 if the 'presqt-source-token' is missing in the headers
        """
        call_get_resource_zip(self)

        header = {}
        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "'presqt-source-token' missing in the request headers.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_401(self):
        """
        Return a 401 if the 'presqt-source-token' provided in the header does not match
        the 'presqt-source-token' in the process_info file.
        """
        call_get_resource_zip(self)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        headers = {'HTTP_PRESQT_SOURCE_TOKEN': '1234'}
        response = self.client.get(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error'],
                         "Header 'presqt-source-token' does not match the 'presqt-source-token' "
                         "for this server process.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_404(self):
        """
        Return a 404 if the ticket_number provided is not a valid ticket number.
        """
        call_get_resource_zip(self)

        url = reverse('download_job', kwargs={'ticket_number': 'bad_ticket'})
        response = self.client.get(url, **self.header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], "Invalid ticket number, 'bad_ticket'.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_401_token_invalid(self):
        """
        Return a 500 if the Resource._download_resource() method running on the server gets a 401 error
        """
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': '1234'}
        call_get_resource_zip(self)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "Token is invalid. Response returned a 401 status code.",
                          'status_code': 401})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_403_unauthorized_container_resource(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 403 error
        """
        self.resource_id = 'q5xmw'
        call_get_resource_zip(self)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "User does not have access to this resource with the token provided.",
                          'status_code': 403})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_403_unauthorized_item_resource(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 403 error
        """
        self.resource_id = '5cd98c2cf244ec0020e4d9d1'
        call_get_resource_zip(self)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "User does not have access to this resource with the token provided.",
                          'status_code': 403})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_404_resource_not_found(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 404 error
        """
        self.resource_id = 'bad_id'
        call_get_resource_zip(self)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "Resource with id 'bad_id' not found for this user.",
                          'status_code': 404})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_410_gone(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 410 error
        """
        self.resource_id = '5cd989c5f8214b00188af9b5'
        call_get_resource_zip(self)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "The requested resource is no longer available.",
                          'status_code': 410})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))
