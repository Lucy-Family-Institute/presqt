import glob
import json

from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import token_validation
from presqt.exceptions import (PresQTValidationError, PresQTAuthorizationError,
                               PresQTResponseException)


class DownloadResource(APIView):
    """
    **Supported HTTP Methods**

    * GET: Prepares a download of a resource with the given resource ID provided. Spawns a
    process separate from the request server to do the actual downloading and zip-file preparation.
    """

    def get(self, request, ticket_number):

        # Perform token validation
        try:
            token = token_validation(request)
        except PresQTAuthorizationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Path to the file to be downloaded
        zip_file_path = glob.glob('mediafiles/downloads/{}/*.zip'.format(
            ticket_number))

        # Path to the process_info file
        process_info_path = 'mediafiles/downloads/{}/process_info.json'.format(
            ticket_number)

        # Get process_info from file
        with open(process_info_path) as process_info:
            data = json.load(process_info)
            download_file_status = data['status']
            print(download_file_status)

        if download_file_status == 'in_progress':
            return Response(status=status.HTTP_202_ACCEPTED,
                            data={'status': download_file_status,
                                  'message': data['message'],
                                  'download_file': None})

        if download_file_status == 'failed':
            return Response(status=status.HTTP_200_OK,
                            data={'status': download_file_status,
                                  'message': data['message'],
                                  'download_file': None})

        if download_file_status == 'finished':
            return Response(status=status.HTTP_200_OK,
                            data={'status': download_file_status,
                                  'message': data['message'],
                                  'download_file': zip_file_path[0]})
