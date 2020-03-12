import json
import multiprocessing
import os

from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import (get_source_token, get_process_info_data,
                                     process_token_validation, hash_tokens)
from presqt.utilities import PresQTValidationError, write_file


class DownloadJob(APIView):
    """
    **Supported HTTP Methods**

    * GET:
        - Check if a resource download is finished on the server matching the ticket number.
          If the download is pending, failed, or the response_format is 'json' then return a JSON
          representation of the state. Otherwise return the file contents.
    * PATCH:
        - Cancel the resource download process on the server.

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
        # Perform token validation. Read data from the process_info file.
        try:
            token = get_source_token(request)
            data = get_process_info_data('downloads', ticket_number)
            process_token_validation(hash_tokens(token), data, 'presqt-source-token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Verify that the only acceptable response format was provided
        if response_format and response_format not in ['json', 'zip']:
            return Response(
                data={'error': 'PresQT Error: {} is not a valid format for this endpoint.'.format(
                    response_format)},
            status=status.HTTP_400_BAD_REQUEST)

        download_status = data['status']
        message = data['message']
        status_code = data['status_code']

    # Return the file to download if it has finished.
        if download_status == 'finished':
            if response_format == 'zip':
                # Path to the file to be downloaded
                zip_name = data['zip_name']
                zip_file_path = os.path.join('mediafiles', 'downloads', ticket_number, zip_name)

                response = HttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename={}'.format(zip_name)
            else:
                response = Response(data={'status_code': status_code,
                                          'message': message,
                                          'failed_fixity': data['failed_fixity']},
                                    status=status.HTTP_200_OK)
            return response
        else:
            if download_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            return Response(status=http_status,
                            data={'status_code': status_code, 'message': message})

    def patch(self, request, ticket_number, response_format=None):
        """
        Cancel the resource download process on the server. Update the process_info.json
        file appropriately.

        Parameters
        ----------
        ticket_number : str
            The ticket number of the download being prepared.
        response_format: str
            For patch, response_format should be JSON or None

        Returns
        -------
        200: OK
        {
            "status_code": "499",
            "message": "Download was cancelled by the user"
        }

        400: Bad Request
        {
            "error": "PresQT Error: 'presqt-source-token' missing in the request headers."
        }
        or
        {
            "error": "PresQT Error: 'zip' is not a valid format for this endpoint."
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

        406: Not Acceptable
        {
            "status_code": "200",
            "message": "Download Successful"
        }
        """
        # Perform token validation. Read data from the process_info file.
        try:
            token = get_source_token(request)
            data = get_process_info_data('downloads', ticket_number)
            process_token_validation(hash_tokens(token), data, 'presqt-source-token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Verify that the only acceptable response format was provided
        if response_format and response_format != 'json':
            return Response(
                data={'error': 'PresQT Error: {} is not a valid format for this endpoint.'.format(
                    response_format)},
                status=status.HTTP_400_BAD_REQUEST)

        # Wait until the spawned off process has started to cancel the download
        while data['function_process_id'] is None:
            try:
                data = get_process_info_data('downloads', ticket_number)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # If download is still in progress then cancel the subprocess
        if data['status'] == 'in_progress':
            for process in multiprocessing.active_children():
                if process.pid == data['function_process_id']:
                    process.terminate()
                    process.join()
                    data['status'] = 'failed'
                    data['message'] = 'Download was cancelled by the user'
                    data['status_code'] = '499'
                    data['expiration'] = str(timezone.now() + relativedelta(hours=1))
                    process_info_path = 'mediafiles/downloads/{}/process_info.json'.format(
                        ticket_number)
                    write_file(process_info_path, data, True)

                    return Response(
                        data={'status_code': data['status_code'], 'message': data['message']},
                        status=status.HTTP_200_OK)
        # If download is finished then don't attempt to cancel subprocess
        else:
            return Response(
                data={'status_code': data['status_code'], 'message': data['message']},
                status=status.HTTP_406_NOT_ACCEPTABLE)
