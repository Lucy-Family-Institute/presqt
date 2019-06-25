import multiprocessing

import bagit

from uuid import uuid4
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


from presqt.api_v1.utilities import (token_validation, target_validation, FunctionRouter,
                                     write_file, zip_directory)
from presqt.api_v1.utilities.io.read_file import read_file
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.exceptions import (PresQTValidationError, PresQTAuthorizationError,
                               PresQTResponseException)
from presqt import fixity


class PrepareDownload(APIView):
    """
    **Supported HTTP Methods**

    * GET: Prepares a download of a resource with the given resource ID provided. Spawns a
    process separate from the request server to do the actual downloading and zip-file preparation.
    """
    def get(self, request, target_name, resource_id):
        """
        Prepare a resource for download.

        Parameters
        ----------
        target_name : str
            The name of the Target resource to retrieve.
        resource_id : str
            The id of the Resource to retrieve.

        Returns
        -------
        202: Accepted
        {
            "ticket_number": "1234567890"
            "message": "The server is processing the request."
        }

        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_download'."
        }
        or
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }
        """
        action = 'resource_download'

        # Perform token validation
        try:
            token = token_validation(request)
        except PresQTAuthorizationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Perform target_name and action validation
        try:
            target_validation(target_name, action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Generate ticket number
        ticket_number = uuid4()

        # Create directory and process_info json file
        process_info_obj = {
            'presqt-source-token': token,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Download is being processed on the server',
            'status_code': None
        }

        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)
        process_info_path = '{}/process_info.json'.format(ticket_path)
        write_file(process_info_path, process_info_obj, True)


        # Create a shared memory map that the watchdog monitors to see if the spawned
        # off process has finished
        process_state = multiprocessing.Value('b', 0)
        # Spawn job separate from request memory thread
        function_process = multiprocessing.Process(target=download_resource, args=[
            target_name, action, token, resource_id, ticket_path, process_info_path, process_state])
        function_process.start()

        # Start the watchdog process that will monitor the spawned off process
        watch_dog = multiprocessing.Process(target=process_watchdog,
                                            args=[function_process, process_info_path,
                                                  3600, process_state])
        watch_dog.start()

        # Get the download url
        reversed_url = reverse('download_resource', kwargs={'ticket_number': ticket_number})
        download_hyperlink = request.build_absolute_uri(reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'download_link': download_hyperlink})


def download_resource(target_name, action, token, resource_id, ticket_path,
                      process_info_path, process_state):
    """
    Downloads the resources from the target, performs a fixity check, zips them up in BagIt format.

    Parameters
    ----------
    target_name : str
        Name of the Target resource to retrieve.
    action : str
        Name of the action being performed.
    token : str
        Token of the user performing the request.
    resource_id: str
        ID of the Resource to retrieve.
    ticket_path : str
        Path to the ticket_id directory that holds all downloads and process_info
    process_info_path : str
        Path to the process_info JSON file
    process_state : memory_map object
        Shared memory map object that the watchdog process will monitor
    """
    # Fetch the proper function to call
    func = FunctionRouter.get_function(target_name, action)

    # Get the current process_info.json data to be used throughout the file
    process_info_data = read_file(process_info_path, True)

    # Fetch the resources. 'resources' will be a list of the following dictionary:
    # {'file': binary_file,
    # 'hashes': {'some_hash': value, 'other_hash': value},
    # 'title': resource_title,
    # 'path': /some/path/to/resource}
    try:
        resources = func(token, resource_id)
    except PresQTResponseException as e:
        # Catch any errors that happen within the target fetch.
        # Update the server process_info file appropriately.
        process_info_data['status_code'] = e.status_code
        process_info_data['status'] = 'failed'
        process_info_data['message'] = e.data
        # Update the expiration from 5 days to 1 hour from now. We can delete this faster because
        # it's an incomplete/failed directory.
        process_info_data['expiration'] = str(timezone.now() + relativedelta(hours=1))
        write_file(process_info_path, process_info_data, True)
        #  Update the shared memory map so the watchdog process can stop running.
        process_state.value = 1
        return

    # The directory all files should be saved in.
    base_file_name = '{}_download_{}'.format(target_name, resource_id)
    base_directory = '{}/{}'.format(ticket_path, base_file_name)

    # For each resource, perform fixity check, and save to disk.
    fixity_info = []
    for resource in resources:
        # Perform the fixity check and add extra info to the returned fixity object.
        fixity_obj = fixity.fixity_checker(
            resource['file'], resource['hashes'])
        fixity_obj['resource_title'] = resource['title']
        fixity_obj['path'] = resource['path']
        fixity_info.append(fixity_obj)

        # Save the file to the disk.
        write_file('{}{}'.format(base_directory, resource['path']), resource['file'])

    # Add the fixity file to the disk directory
    write_file('{}/fixity_info.json'.format(base_directory), fixity_info, True)

    # Make a Bagit 'bag' of the resources.
    bagit.make_bag(base_directory)

    # Zip the Bagit 'bag' to send forward.
    zip_directory("{}/{}.zip".format(ticket_path, base_file_name), base_directory, ticket_path)

    # Everything was a success so update the server metadata file.
    process_info_data['status_code'] = '200'
    process_info_data['status'] = 'finished'
    process_info_data['message'] = 'Download successful'
    process_info_data['zip_name'] = '{}.zip'.format(base_file_name)
    write_file(process_info_path, process_info_data, True)

    # Update the shared memory map so the watchdog process can stop running.
    process_state.value = 1
    return


class DownloadResource(APIView):
    """
    **Supported HTTP Methods**

    * GET: Check if a resource download is finished on the server matching the ticket number.  If it
    is then download it otherwise return the state of it.
    """

    def get(self, request, ticket_number):
        """
        Offer the resource for download.

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
            token = token_validation(request)
        except PresQTAuthorizationError as e:
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