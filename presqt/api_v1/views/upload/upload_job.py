from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from presqt.api_v1.utilities import (get_destination_token, get_process_info_data,
                                     process_token_validation)
from presqt.utilities import PresQTValidationError


class UploadJob(APIView):
    """
    **Supported HTTP Methods**

    * GET:
        - Check if a given resource upload is finished.
    """
    def get(self, request, ticket_number):
        """
        Check in on the resource's upload process state.

        Parameters
        ----------
        ticket_number : str
            The ticket number of the upload being prepared.

        Returns
        -------
        200: OK
        {
            "status_code": "200",
            "message": "Upload successful",
            "failed_fixity": [],
            "duplicate_files_ignored": [],
            "duplicate_files_updated": []
        }

        202: Accepted
        {
            "status": "in_progress",
            "message": "Upload is being processed on the server"
        }

        400: Bad Request
        {
            "error": "'presqt-destination-token' missing in the request headers."
        }

        401: Unauthorized
        {
            "error": "Header 'presqt-destination-token' does not match the
            'presqt-destination-token' for this server process."
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
            token = get_destination_token(request)
            process_data = get_process_info_data('uploads', ticket_number)
            process_token_validation(token, process_data, 'presqt-destination-token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        download_status = process_data['status']
        data = {'status_code': process_data['status_code'], 'message': process_data['message']}

        if download_status == 'finished':
            http_status = status.HTTP_200_OK
            data['failed_fixity'] = process_data['failed_fixity']
            data['duplicate_files_ignored'] = process_data['duplicate_files_ignored']
            data['duplicate_files_updated'] = process_data['duplicate_files_updated']
        else:
            if download_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(status=http_status, data=data)
