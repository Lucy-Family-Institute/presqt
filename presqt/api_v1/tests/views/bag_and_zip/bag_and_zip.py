import io
import zipfile

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient


class TestBagAndZipGET(SimpleTestCase):
    """
    Test the `api_v1/get_and_bag` endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('bag_and_zip')

    def test_success(self):
        file = 'presqt/api_v1/tests/resources/upload/bagless_zip.zip'
        response = self.client.post(self.url, {'presqt-file': open(file, 'rb')})
        self.assertEquals(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        self.assertEqual(len(zip_file.namelist()), 11)

    def test_not_a_zip(self):
        file = 'presqt/api_v1/tests/resources/upload/screenshot.png'
        response = self.client.post(self.url, {'presqt-file': open(file, 'rb')})
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'error': "PresQT Error: The file provided, 'presqt-file', is not a zip file."})

    def test_no_file(self):
        response = self.client.post(self.url)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'error': "PresQT Error: The file, 'presqt-file', is not found in the body of the request."})







