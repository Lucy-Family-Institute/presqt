import os

from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import (get_source_token, get_process_info_data,
                                     process_token_validation, hash_tokens)
from presqt.utilities import PresQTValidationError


class DownloadJob(APIView):
    """
    **Supported HTTP Methods**

    * GET:
        - Check if a resource download is finished on the server matching the ticket number.
          If it is then download it otherwise return the state of it.
    """

    def get(self, request, ticket_number):
        """
        Check in on the resource's download process state.

        Parameters
        ----------
        ticket_number : str
            The ticket number of the download being prepared.

        Returns
        -------
        200: OK
        Returns the zip of resources to be downloaded.

        202: Accepted
        {
            "status_code": null,
            "message": "Download is being processed on the server"
        }

        400: Bad Request
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        401: Unauthorized
        {
            "error": "Header 'presqt-source-token' does not match the
            'presqt-source-token' for this server process."
        }

        404: Not Found
        {
            "error": "Invalid ticket number, '1234'."
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

        download_status = data['status']
        message = data['message']
        status_code = data['status_code']

        # Return the file to download if it has finished.
        if download_status == 'finished':
            # Path to the file to be downloaded
            zip_name = data['zip_name']
            zip_file_path = os.path.join('mediafiles', 'downloads', ticket_number, zip_name)

            response = HttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename={}'.format(zip_name)
            return response
        else:
            if download_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            return Response(status=http_status,
                            data={'status_code': status_code, 'message': message})
