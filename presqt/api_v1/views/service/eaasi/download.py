import os

from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import (get_process_info_data, process_token_validation,
                                     get_source_token, hash_tokens, get_process_info_action)
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
        or
        {
            "error": "PresQT Error: Invalid ticket number, '1233'."
        }
        or
        {
            "error": "PresQT Error: A resource_download does not exist for this user on the server."
        }
        """
        try:
            eaasi_token = request.query_params['eaasi_token']
        except MultiValueDictKeyError:
            return Response(data={'error': "'eaasi_token' not found as query parameter."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Get the source token from the request, hash it to get the ticket_number, get the
        # process info data for resource_download
        try:
            process_info_data = get_process_info_data(ticket_number)
            download_data = get_process_info_action(process_info_data, 'resource_download')
            process_token_validation(eaasi_token, download_data, 'eaasi_token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Return the file to download if it has finished.
        if download_data['status'] == 'finished':
            # Path to the file to be downloaded
            zip_name = download_data['zip_name']
            zip_file_path = os.path.join('mediafiles', 'jobs', ticket_number, zip_name)

            response = HttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename={}'.format(zip_name)
        else:
            response = Response(data={'message': 'File unavailable.'}, status=status.HTTP_404_NOT_FOUND)
        return response

