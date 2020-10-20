import os
import zipfile
from uuid import uuid4

import bagit
from django.http import HttpResponse
from rest_framework import renderers
from rest_framework.views import APIView
from rest_framework.response import Response

from presqt.api_v1.utilities.validation.file_validation import file_validation
from presqt.utilities import PresQTValidationError, zip_directory


class BagAndZip(APIView):
    """
    **Supported HTTP Methods**

    * POST:
        - Take a provided file, make it BagIt format, and zip it up to return back to the user.
    """

    renderer_classes = [renderers.JSONRenderer]

    def post(self, request):
        """
        Take a zipped file, format it using BagIt, and return it to the user.

        Returns
        -------
        200: OK
        Returns a file

        400: Bad Request
        {
            "error": "PresQT Error: The file, 'presqt-file', is not found in the body of the request."
        }
        or
        {
            "error": "PresQT Error: The file provided, 'presqt-file', is not a zip file."
        }

        """
        ignore_list = ['.DS_Store', '__MACOSX', 'thumbs.db', 'desktop.ini']
        try:
            request_file = file_validation(request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        ticket_number = uuid4()
        ticket_path = os.path.join("mediafiles", 'bag_tool', str(ticket_number))
        data_path = os.path.join(ticket_path, 'presqt_bag')

        # Extract each file in the zip file to disk
        with zipfile.ZipFile(request_file) as myzip:
            file_name = myzip.filename
            for name in myzip.namelist():
                if name.partition('/')[0] in ignore_list or name.rpartition('/')[2] in ignore_list:
                    continue
                myzip.extract(name, data_path)

        # Make a BagIt 'bag' of the resources.
        bagit.make_bag(data_path, checksums=['md5', 'sha1', 'sha256', 'sha512'])

        # Zip the BagIt 'bag' to send forward.
        zip_path = os.path.join(ticket_path, "presqt_bag.zip")
        zip_directory(data_path, zip_path, ticket_path)

        response = HttpResponse(open(zip_path, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=presqt_{}'.format(file_name)

        return response
