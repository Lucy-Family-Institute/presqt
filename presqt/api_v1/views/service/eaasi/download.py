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
    **Supported HTTP Methods**

    * GET:
        - Check if a resource download is finished on the server matching the ticket number.
          If the download is pending, failed, then return a JSON representation of the state. 
          Otherwise return the file contents.
    """

    def get(self, request, ticket_number):
        """
        Get the resource's download contents.

        Parameters
        ----------
        ticket_number: str
            The ticket number of the download being prepared.
        
        Returns
        -------
        200: OK
        Returns the zip of resources to be downloaded.
        
        400: Bad Request
        {
            "error": "'eaasi_token' not found as query parameter."
        }

        401: Unauthorized
        {
            "PresQT Error: Header 'eaasi_token' does not match the 'eaasi_token' for this server process."
        }
        
        404: Not Found
        {
            "message": "File unavailable."
        }
        """
        try:
            token = request.query_params['eaasi_token']
        except MultiValueDictKeyError:
            return Response(data={'error': "'eaasi_token' not found as query parameter."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Perform token validation. Read data from the process_info file.
        try:
            data = get_process_info_data('downloads', ticket_number)
            process_token_validation(token, data, 'eaasi_token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Return the file to download if it has finished.
        if data['status'] == 'finished':
            # Path to the file to be downloaded
            zip_name = data['zip_name']
            zip_file_path = os.path.join('mediafiles', 'downloads', ticket_number, zip_name)

            response = HttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename={}'.format(zip_name)
        else:
            response = Response(data={'message': 'File unavailable.'}, status=status.HTTP_404_NOT_FOUND)
        
        return response

