import json
import multiprocessing

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from presqt.api_v1.utilities import (get_destination_token, get_process_info_data,
                                     process_token_validation, get_source_token, hash_tokens)
from presqt.utilities import PresQTValidationError, write_file


class TransferJob(APIView):
    """
    **Supported HTTP Methods**

    * GET:
        - Check if a given resource transfer is finished.
    """

    def get(self, request, ticket_number):
        """
        Check in on the resource's transfer process state.

        Parameters
        ----------
        ticket_number : str
            The ticket number of the transfer being prepared.

        Returns
        -------
        200: OK
        """
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(request)
            source_token = get_source_token(request)
            process_data = get_process_info_data('transfers', ticket_number)
            process_token_validation(hash_tokens(destination_token),
                                     process_data, 'presqt-destination-token')
            process_token_validation(hash_tokens(source_token), process_data, 'presqt-source-token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        transfer_status = process_data['status']
        data = {'status_code': process_data['status_code'], 'message': process_data['message']}

        if transfer_status == 'finished':
            http_status = status.HTTP_200_OK
            data['failed_fixity'] = process_data['failed_fixity']
            data['resources_ignored'] = process_data['resources_ignored']
            data['resources_updated'] = process_data['resources_updated']
        else:
            if transfer_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(status=http_status, data=data)

    def patch(self, request, ticket_number):
        """
        Cancel the resource transfer process on the server. Update the process_info.json
        file appropriately.

        Parameters
        ----------
        ticket_number : str
            The ticket number of the transfer being prepared.

        Returns
        -------
        200: OK
        {
            "status_code": "410",
            "message": "Transfer was cancelled by the user"
        }

        400: Bad Request
        {
            "error": "'presqt-destination-token' missing in the request headers."
        }

        400: Bad Request
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        401: Unauthorized
        {
            "error": "Header 'presqt-destination-token' does not match the
            'presqt-destination-token' for this server process."
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

        406: Not Acceptable
        {
            "status_code": "200",
            "message": "Transfer Successful"
        }
        """
        # Perform token validation. Read data from the process_info file.
        try:
            token = get_destination_token(request)
            source_token = get_source_token(request)
            process_data = get_process_info_data('transfers', ticket_number)
            process_token_validation(hash_tokens(token), process_data, 'presqt-destination-token')
            process_token_validation(hash_tokens(source_token), process_data, 'presqt-source-token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Wait until the spawned off process has started to cancel the transfer
        while process_data['function_process_id'] is None:
            try:
                process_data = get_process_info_data('transfers', ticket_number)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        if process_data['status'] == 'in_progress':
            for process in multiprocessing.active_children():
                if process.pid == process_data['function_process_id']:
                    process.terminate()
                    process.join()
                    process_data['status'] = 'failed'
                    process_data['message'] = 'Transfer was cancelled by the user'
                    process_data['status_code'] = '410' # CHANGE THIS STATUS CODE
                    process_data['expiration'] = str(timezone.now() + relativedelta(hours=1))
                    process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
                        ticket_number)
                    write_file(process_info_path, process_data, True)

                    return Response(
                        data={'status_code': process_data['status_code'], 'message': process_data['message']},
                        status=status.HTTP_200_OK)
        else:
            return Response(
                data={'status_code': process_data['status_code'], 'message': process_data['message']},
                status=status.HTTP_406_NOT_ACCEPTABLE)