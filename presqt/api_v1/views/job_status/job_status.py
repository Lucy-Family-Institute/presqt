import json
import multiprocessing
import os

from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from presqt.api_v1.utilities import (get_source_token, get_process_info_data, hash_tokens,
                                     update_or_create_process_info, get_destination_token,
                                     process_token_validation)
from presqt.utilities import PresQTValidationError, write_file


class JobStatus(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve the status of a job
    """
    def get(self, request, action, response_format=None):
        """
        Retrieve the status of a job

        Path Parameters
        ---------------
        action: str
            The action to get the status of

        Returns
        -------
        200: OK
        A dictionary like JSON representation of the requested job status

        400: Bad Request
        {
            "error": "PresQT Error: 'presqt-source-token' missing in the request headers."
        }
        or
        {
            "error": "PresQT Error: {} is not a valid acton."
        }
        404  Not Found
        {
            "error": "PresQT Error: Invalid ticket number, '1234'."
        }
        """
        self.response_format = response_format

        try:
            func = getattr(self, '{}_get'.format(action))
        except AttributeError:
            return Response(data={"error": "PresQT Error: {} is not a valid acton.".format(action)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return func()

    def collection_get(self):
        # Perform token validation. Read data from the process_info file.
        try:
            source_token = get_source_token(self.request)
            self.ticket_number = hash_tokens(source_token)
            self.process_data = get_process_info_data('jobs', self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        data = {
            'total_files': self.process_data['resource_collection']['total_files'],
            'files_finished': self.process_data['resource_collection']['files_finished']
        }
        return Response(status=status.HTTP_200_OK, data=data)

    def download_get(self):
        # Perform token validation. Read data from the process_info file.
        try:
            source_token = get_source_token(self.request)
            self.ticket_number = hash_tokens(source_token)
            self.process_data = get_process_info_data('jobs', self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Verify that the only acceptable response format was provided.
        if self.response_format and self.response_format not in ['json', 'zip']:
            return Response(
                data={'error': 'PresQT Error: {} is not a valid format for this endpoint.'.format(
                    self.response_format)},
                status=status.HTTP_400_BAD_REQUEST)

        download_process_data = self.process_data['resource_download']
        download_status = download_process_data['status']
        message = download_process_data['message']
        status_code = download_process_data['status_code']

        # Return the file to download if it has finished.
        if download_status == 'finished':
            if self.response_format == 'zip':
                # Path to the file to be downloaded
                zip_name = download_process_data['zip_name']
                zip_file_path = os.path.join('mediafiles', 'jobs', self.ticket_number, zip_name)

                response = HttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename={}'.format(zip_name)
            else:
                response = Response(data={'status_code': status_code,
                                          'message': message,
                                          'zip_name': download_process_data['zip_name'],
                                          'failed_fixity': download_process_data['failed_fixity']},
                                    status=status.HTTP_200_OK)
            return response
        else:
            if download_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            return Response(status=http_status,
                            data={'status_code': status_code, 'message': message})

    def upload_get(self):
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(self.request)
            self.ticket_number = hash_tokens(destination_token)
            self.process_data = get_process_info_data('jobs', self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        upload_process_data = self.process_data['resource_upload']

        upload_status = upload_process_data['status']
        data = {'status_code': upload_process_data['status_code'], 'message': upload_process_data['message']}

        if upload_status == 'finished':
            http_status = status.HTTP_200_OK
            data['failed_fixity'] = upload_process_data['failed_fixity']
            data['resources_ignored'] = upload_process_data['resources_ignored']
            data['resources_updated'] = upload_process_data['resources_updated']
        else:
            if upload_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(status=http_status, data=data)

    def transfer_get(self):
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(self.request)
            source_token = get_source_token(self.request)
            self.ticket_number = '{}_{}'.format(hash_tokens(source_token),
                                                hash_tokens(destination_token))
            self.process_data = get_process_info_data('jobs', self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        transfer_process_data = self.process_data['resource_transfer_in']
        transfer_status = transfer_process_data['status']
        data = {'status_code': transfer_process_data['status_code'],
                'message': transfer_process_data['message']}

        if transfer_status == 'finished':
            http_status = status.HTTP_200_OK
            data['failed_fixity'] = transfer_process_data['failed_fixity']
            data['resources_ignored'] = transfer_process_data['resources_ignored']
            data['resources_updated'] = transfer_process_data['resources_updated']
            data['enhanced_keywords'] = transfer_process_data['enhanced_keywords']
            data['initial_keywords'] = transfer_process_data['initial_keywords']
            data['source_resource_id'] = transfer_process_data['source_resource_id']
            data['destination_resource_id'] = transfer_process_data['destination_resource_id']
        else:
            if transfer_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(status=http_status, data=data)

    def patch(self, request, action, response_format=None):
        self.response_format = response_format

        try:
            func = getattr(self, '{}_patch'.format(action))
        except AttributeError:
            return Response(data={"error": "PresQT Error: {} is not a valid acton.".format(action)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return func()

    def download_patch(self):
        # Perform token validation. Read data from the process_info file.
        try:
            source_token = get_source_token(self.request)
            self.ticket_number = hash_tokens(source_token)
            self.process_data = get_process_info_data('jobs', self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Verify that the only acceptable response format was provided
        if self.response_format and self.response_format != 'json':
            return Response(
                data={'error': 'PresQT Error: {} is not a valid format for this endpoint.'.format(
                    self.response_format)},
                status=status.HTTP_400_BAD_REQUEST)

        # Wait until the spawned off process has started to cancel the download
        while self.process_data['resource_download']['function_process_id'] is None:
            try:
                self.process_data = get_process_info_data('jobs', self.ticket_number)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_process_data = self.process_data['resource_download']

        # If download is still in progress then cancel the subprocess
        if download_process_data['status'] == 'in_progress':
            for process in multiprocessing.active_children():
                if process.pid == download_process_data['function_process_id']:
                    process.kill()
                    process.join()
                    download_process_data['status'] = 'failed'
                    download_process_data['message'] = 'Download was cancelled by the user'
                    download_process_data['status_code'] = '499'
                    download_process_data['expiration'] = str(timezone.now() + relativedelta(hours=1))
                    update_or_create_process_info(download_process_data, 'resource_download', self.ticket_number)


                return Response(
                        data={'status_code': download_process_data['status_code'], 'message': download_process_data['message']},
                        status=status.HTTP_200_OK)
        # If download is finished then don't attempt to cancel subprocess
        else:
            return Response(
                data={'status_code': download_process_data['status_code'], 'message': download_process_data['message']},
                status=status.HTTP_406_NOT_ACCEPTABLE)

    def upload_patch(self):
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(self.request)
            self.ticket_number = hash_tokens(destination_token)
            self.process_data = get_process_info_data('jobs', self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Wait until the spawned off process has started to cancel the upload
        while self.process_data['resource_upload']['function_process_id'] is None:
            try:
                self.process_data = get_process_info_data('jobs', self.ticket_number)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_process_data = self.process_data['resource_upload']

        # If upload is still in progress then cancel the subprocess
        if upload_process_data['status'] == 'in_progress':
            for process in multiprocessing.active_children():
                if process.pid == upload_process_data['function_process_id']:
                    process.kill()
                    process.join()
                    upload_process_data['status'] = 'failed'
                    upload_process_data['message'] = 'Upload was cancelled by the user'
                    upload_process_data['status_code'] = '499'
                    upload_process_data['expiration'] = str(timezone.now() + relativedelta(hours=1))
                    update_or_create_process_info(upload_process_data, 'resource_upload', self.ticket_number)
                    return Response(
                        data={'status_code': upload_process_data['status_code'], 'message': upload_process_data['message']},
                        status=status.HTTP_200_OK)
        # If upload is finished then don't attempt to cancel subprocess
        else:
            return Response(
                data={'status_code': upload_process_data['status_code'], 'message': upload_process_data['message']},
                status=status.HTTP_406_NOT_ACCEPTABLE)

    def transfer_patch(self):
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(self.request)
            source_token = get_source_token(self.request)
            self.ticket_number = '{}_{}'.format(hash_tokens(source_token),
                                                hash_tokens(destination_token))
            process_data = get_process_info_data('jobs', self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Wait until the spawned off process has started to cancel the transfer
        while process_data['function_process_id'] is None:
            try:
                process_data = get_process_info_data('jobs', self.ticket_number)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        transfer_process_data = self.process_data['resource_transfer_in']

        # If transfer is still in progress then cancel the subprocess
        if transfer_process_data['status'] == 'in_progress':
            for process in multiprocessing.active_children():
                if process.pid == transfer_process_data['function_process_id']:
                    process.kill()
                    process.join()
                    transfer_process_data['status'] = 'failed'
                    transfer_process_data['message'] = 'Transfer was cancelled by the user'
                    transfer_process_data['status_code'] = '499'
                    transfer_process_data['expiration'] = str(timezone.now() + relativedelta(hours=1))
                    update_or_create_process_info(transfer_process_data, 'resource_transfer_in', self.ticket_number)
                    return Response(
                        data={'status_code': process_data['status_code'], 'message': process_data['message']},
                        status=status.HTTP_200_OK)
        # If transfer is finished then don't attempt to cancel subprocess
        else:
            return Response(
                data={'status_code': process_data['status_code'], 'message': process_data['message']},
                status=status.HTTP_406_NOT_ACCEPTABLE)