from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import source_token_validation
from presqt.api_v1.utilities.io.read_file import read_file
from presqt.exceptions import PresQTValidationError


class DownloadResource(APIView):
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
            "status": "in_progress",
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

        500: Internal Server Error
        {
            "status_code": "404",
            "message": "Resource with id 'bad_id' not found for this user."
        }
        """
        # Perform token validation
        try:
            token = source_token_validation(request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Read data from the process_info file
        data = read_file('mediafiles/downloads/{}/process_info.json'.format(
            ticket_number), True)

        # Ensure that the header token is the same one listed in the process_info file
        if token != data['presqt-source-token']:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={'error': ("Header 'presqt-source-token' does not match the "
                                            "'presqt-source-token' for this server process.")})

        download_status = data['status']
        message = data['message']
        status_code = data['status_code']

        # Return the file to download if it has finished.
        if download_status == 'finished':
            # Path to the file to be downloaded
            zip_name = data['zip_name']
            zip_file_path = 'mediafiles/downloads/{}/{}'.format(ticket_number, zip_name)

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