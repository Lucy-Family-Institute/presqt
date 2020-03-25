import json
import multiprocessing
import os

from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import (get_source_token, get_process_info_data,
                                     process_token_validation, hash_tokens)
from presqt.utilities import PresQTValidationError, write_file


class EaasiDownload(APIView):
    """
    **Supported HTTP Methods**

    * GET:
        - Check if a resource download is finished on the server matching the ticket number.
          If the download is pending, failed, or the response_format is 'json' then return a JSON
          representation of the state. Otherwise return the file contents.
    """

    def get(self, request, ticket_number, response_format=None):
        """
        Check in on the resource's download process state.

        Parameters
        ----------
        ticket_number : str
            The ticket number of the download being prepared.
        response_format: str
            The type of response to return. Either json or zip

        Returns
        -------
        200: OK
        Returns the zip of resources to be downloaded.
        or
        {
            "status_code": "200",
            "message": "Download successful but with fixity errors.",
            "failed_fixity": ["/Character Sheet - Alternative - Print Version.pdf"]
        }

        202: Accepted
        {
            "status_code": null,
            "message": "Download is being processed on the server"
        }

        400: Bad Request
        {
            "error": "PresQT Error: 'presqt-source-token' missing in the request headers."
        }
        or
        {
            "error": "PresQT Error: 'csv' is not a valid format for this endpoint."
        }

        401: Unauthorized
        {
            "error": "PresQT Error: Header 'presqt-source-token' does not match the
            'presqt-source-token' for this server process."
        }

        404: Not Found
        {
            "error": "PresQT Error: Invalid ticket number, '1234'."
        }

        500: Internal Server Error
        {
            "status_code": "404",
            "message": "Resource with id 'bad_id' not found for this user."
        }
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

