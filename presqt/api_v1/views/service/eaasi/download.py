import os

from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import (get_process_info_data, process_token_validation)
from presqt.utilities import PresQTValidationError


class EaasiDownload(APIView):
    """
    """

    def get(self, request, ticket_number):
        """

        200
        400
        404
        404
        401
        """
        try:
            token = request.query_params['eaasi_token']
        except MultiValueDictKeyError:
            return Response(data={'error': "'eaasi_token' or 'format' not found as query parameter."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Perform token validation. Read data from the process_info file.
        try:
            data = get_process_info_data('downloads', ticket_number)
            process_token_validation(token, data, 'eaasi_token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        download_status = data['status']

        # Return the file to download if it has finished.
        if download_status == 'finished':
            # Path to the file to be downloaded
            zip_name = data['zip_name']
            zip_file_path = os.path.join('mediafiles', 'downloads', ticket_number, zip_name)

            response = HttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename={}'.format(zip_name)
        else:
            response = Response(data={'message': 'File unavailable.'}, status=status.HTTP_404_NOT_FOUND)
        
        return response

