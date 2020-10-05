import json
import multiprocessing
import os

from dateutil.relativedelta import relativedelta
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from presqt.api_v1.utilities import (get_source_token, get_process_info_data, hash_tokens,
                                     update_or_create_process_info, get_destination_token,
                                     process_token_validation, calculate_job_percentage)
from presqt.utilities import PresQTValidationError, write_file


class JobStatus(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve the status of a job
    * Patch: Cancel a job
    """

    def get(self, request, action, response_format=None):
        """
        Retrieve the status of a job.

        Handler for all action status jobs...will route to the correct action class method
        depending on the action url parameter, 'action'.

        Path Parameters
        ---------------
        action: str
            The action to get the status of
        response_format:
            Optional parameter for specifying the response format for downloads

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
        or
        {
            "error": 'PresQT Error: Bad token provided'
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
            return Response(data={"error": "PresQT Error: '{}' is not a valid acton.".format(action)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return func()

    def download_get(self):
        """
        Get the status of a download job.

        Will return either a json object or a file bytes depending on the 'resource_format' url
        parameter
        """
        if self.request.query_params:
            try:
                # This check will run for the email links we generate
                self.ticket_number = self.request.query_params['ticket_number']
                self.process_data = get_process_info_data(self.ticket_number)
            except (MultiValueDictKeyError, PresQTValidationError):
                return Response(data={'error': "'ticket_number' not found as query parameter or invalid 'ticket_number' provided."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            # Perform token validation. Read data from the process_info file.
            try:
                source_token = get_source_token(self.request)
                self.ticket_number = hash_tokens(source_token)
                self.process_data = get_process_info_data(self.ticket_number)
            except PresQTValidationError as e:
                return Response(data={'error': e.data}, status=e.status_code)

        # Verify that the only acceptable response format was provided.
        if self.response_format and self.response_format not in ['json', 'zip']:
            return Response(
                data={'error': 'PresQT Error: {} is not a valid format for this endpoint.'.format(
                    self.response_format)},
                status=status.HTTP_400_BAD_REQUEST)
        try:
            download_process_data = self.process_data['resource_download']
        except KeyError:
            return Response(
                data={'error': 'PresQT Error: "resource_download" not found in process_info file.'},
                status=status.HTTP_400_BAD_REQUEST)

        download_status = download_process_data['status']
        message = download_process_data['message']
        status_code = download_process_data['status_code']

        total_files = download_process_data['download_total_files']
        files_finished = download_process_data['download_files_finished']
        download_job_percentage = calculate_job_percentage(total_files, files_finished)

        # Return the file to download if it has finished.
        if download_status == 'finished':
            if self.response_format == 'zip':
                # Path to the file to be downloaded
                zip_name = download_process_data['zip_name']
                zip_file_path = os.path.join('mediafiles', 'jobs', self.ticket_number,
                                             'download', zip_name)

                response = HttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename={}'.format(zip_name)
            else:
                response = Response(data={'status_code': status_code,
                                          'message': message,
                                          'zip_name': download_process_data['zip_name'],
                                          'failed_fixity': download_process_data['failed_fixity'],
                                          'job_percentage': download_job_percentage,
                                          'status': download_status
                                          },
                                    status=status.HTTP_200_OK)
            return response
        else:
            if download_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            return Response(status=http_status,
                            data={'job_percentage': download_job_percentage,
                                  'status': download_status,
                                  'status_code': status_code,
                                  'message': message
                                  })

    def upload_get(self):
        """
        Get the status of an upload job.
        """
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(self.request)
            self.ticket_number = hash_tokens(destination_token)
            self.process_data = get_process_info_data(self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        try:
            upload_process_data = self.process_data['resource_upload']
        except KeyError:
            return Response(
                data={'error': 'PresQT Error: "resource_upload" not found in process_info file.'},
                status=status.HTTP_400_BAD_REQUEST)

        upload_status = upload_process_data['status']
        total_files = upload_process_data['upload_total_files']
        files_finished = upload_process_data['upload_files_finished']

        job_percentage = calculate_job_percentage(total_files, files_finished)
        data = {
            'status_code': upload_process_data['status_code'],
            'status': upload_status,
            'message': upload_process_data['message'],
            'job_percentage': job_percentage
        }

        if upload_status == 'finished':
            http_status = status.HTTP_200_OK
            data['status'] = upload_status
            data['failed_fixity'] = upload_process_data['failed_fixity']
            data['resources_ignored'] = upload_process_data['resources_ignored']
            data['resources_updated'] = upload_process_data['resources_updated']
            data['job_percentage'] = 99
        else:
            if upload_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
                data['job_percentage'] = job_percentage
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(status=http_status, data=data)

    def transfer_get(self):
        """
        Get the status of a transfer job.
        """
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(self.request)
            source_token = get_source_token(self.request)
            self.ticket_number = '{}_{}'.format(hash_tokens(source_token),
                                                hash_tokens(destination_token))
            self.process_data = get_process_info_data(self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        try:
            transfer_process_data = self.process_data['resource_transfer_in']
        except KeyError:
            return Response(
                data={'error': 'PresQT Error: "resource_download" not found in process_info file.'},
                status=status.HTTP_400_BAD_REQUEST)

        transfer_status = transfer_process_data['status']
        upload_job_percentage = calculate_job_percentage(transfer_process_data['upload_total_files'],
                                                         transfer_process_data['upload_files_finished'])
        download_job_percentage = calculate_job_percentage(transfer_process_data['download_total_files'],
                                                           transfer_process_data['download_files_finished'])
        data = {'status_code': transfer_process_data['status_code'],
                'status': transfer_status,
                'message': transfer_process_data['message'],
                'job_percentage': round((upload_job_percentage + download_job_percentage) / 2),
                }

        if transfer_status == 'finished':
            http_status = status.HTTP_200_OK
            data['failed_fixity'] = transfer_process_data['failed_fixity']
            data['resources_ignored'] = transfer_process_data['resources_ignored']
            data['resources_updated'] = transfer_process_data['resources_updated']
            data['enhanced_keywords'] = transfer_process_data['enhanced_keywords']
            data['initial_keywords'] = transfer_process_data['initial_keywords']
            data['source_resource_id'] = transfer_process_data['source_resource_id']
            data['destination_resource_id'] = transfer_process_data['destination_resource_id']
            data['job_percentage'] = 99
        else:
            if transfer_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(status=http_status, data=data)

    def patch(self, request, action, response_format=None):
        """
        Cancel a job

        Handler for all action status jobs...will route to the correct action class method
        depending on the action url parameter, 'action'.

        Path Parameters
        ---------------
        action: str
            The action to get the status of
        response_format:
            Optional parameter for specifying the response format for downloads

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
        or
        {
            "error": 'PresQT Error: Bad token provided'
        }
        404  Not Found
        {
            "error": "PresQT Error: Invalid ticket number, '1234'."
        }
        """
        self.response_format = response_format

        try:
            func = getattr(self, '{}_patch'.format(action))
        except AttributeError:
            return Response(data={"error": "PresQT Error: {} is not a valid acton.".format(action)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return func()

    def download_patch(self):
        """
        Attempt to cancel a download job.
        """
        # Perform token validation. Read data from the process_info file.
        try:
            source_token = get_source_token(self.request)
            self.ticket_number = hash_tokens(source_token)
            self.process_data = get_process_info_data(self.ticket_number)
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
                self.process_data = get_process_info_data(self.ticket_number)
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
                    download_process_data['expiration'] = str(
                        timezone.now() + relativedelta(hours=1))
                    update_or_create_process_info(
                        download_process_data, 'resource_download', self.ticket_number)

                return Response(
                    data={
                        'status_code': download_process_data['status_code'], 'message': download_process_data['message']},
                    status=status.HTTP_200_OK)
        # If download is finished then don't attempt to cancel subprocess
        else:
            return Response(
                data={
                    'status_code': download_process_data['status_code'], 'message': download_process_data['message']},
                status=status.HTTP_406_NOT_ACCEPTABLE)

    def upload_patch(self):
        """
        Attempt to cancel an upload job.
        """
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(self.request)
            self.ticket_number = hash_tokens(destination_token)
            self.process_data = get_process_info_data(self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Wait until the spawned off process has started to cancel the upload
        while self.process_data['resource_upload']['function_process_id'] is None:
            try:
                self.process_data = get_process_info_data(self.ticket_number)
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
                    update_or_create_process_info(
                        upload_process_data, 'resource_upload', self.ticket_number)
                    return Response(
                        data={
                            'status_code': upload_process_data['status_code'], 'message': upload_process_data['message']},
                        status=status.HTTP_200_OK)
        # If upload is finished then don't attempt to cancel subprocess
        else:
            return Response(
                data={'status_code': upload_process_data['status_code'],
                      'message': upload_process_data['message']},
                status=status.HTTP_406_NOT_ACCEPTABLE)

    def transfer_patch(self):
        """
        Attempt to cancel a transfer job.
        """
        # Perform token validation. Read data from the process_info file.
        try:
            destination_token = get_destination_token(self.request)
            source_token = get_source_token(self.request)
            self.ticket_number = '{}_{}'.format(hash_tokens(source_token),
                                                hash_tokens(destination_token))
            process_data = get_process_info_data(self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Wait until the spawned off process has started to cancel the transfer
        while process_data['resource_transfer_in']['function_process_id'] is None:
            try:
                process_data = get_process_info_data(self.ticket_number)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        transfer_process_data = process_data['resource_transfer_in']

        # If transfer is still in progress then cancel the subprocess
        if transfer_process_data['status'] == 'in_progress':
            for process in multiprocessing.active_children():
                if process.pid == transfer_process_data['function_process_id']:
                    process.kill()
                    process.join()
                    transfer_process_data['status'] = 'failed'
                    transfer_process_data['message'] = 'Transfer was cancelled by the user'
                    transfer_process_data['status_code'] = '499'
                    transfer_process_data['expiration'] = str(
                        timezone.now() + relativedelta(hours=1))
                    update_or_create_process_info(
                        transfer_process_data, 'resource_transfer_in', self.ticket_number)
                    return Response(
                        data={
                            'status_code': transfer_process_data['status_code'], 'message': transfer_process_data['message']},
                        status=status.HTTP_200_OK)
        # If transfer is finished then don't attempt to cancel subprocess
        else:
            return Response(
                data={
                    'status_code': transfer_process_data['status_code'], 'message': transfer_process_data['message']},
                status=status.HTTP_406_NOT_ACCEPTABLE)
