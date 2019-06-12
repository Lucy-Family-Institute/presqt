import multiprocessing
import bagit
import glob

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
from presqt.exceptions import (PresQTValidationError, PresQTAuthorizationError,
                               PresQTResponseException)
from presqt import fixity


class DownloadResource(APIView):
    """
    **Supported HTTP Methods**

    * GET: 
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
        Returns the files/folders to be downloaded

        202: Accepted
        {
            "status": "in_progress",
            "message": "Download is being processed on the server"
        }

        401: Unauthorized
        {
            "error": "Header does not match the request token for this file."
        }

        417: Expectation Failed
        {
            "status": "failed",
            "message": "Resource with id 'eggyboi' not found for this user."
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
        if (request.META['HTTP_PRESQT_SOURCE_TOKEN']) != data['presqt-source-token']:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={'error': 'Header does not match the request token for this file.'})

        # Path to the file to be downloaded
        zip_file_path = glob.glob('mediafiles/downloads/{}/*.zip'.format(
            ticket_number))

        download_file_status = data['status']
        message = data['message']

        # Return the file to download if it has finished.
        if download_file_status == 'finished':
            response = HttpResponse(open(zip_file_path[0], 'rb'),
                                    content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename= {}.zip'.format(
                ticket_number)
            return response

        else:
            if download_file_status == 'in_progress':
                http_status = status.HTTP_202_ACCEPTED
            else:
                http_status = status.HTTP_417_EXPECTATION_FAILED

            return Response(status=http_status,
                            data={'status': download_file_status,
                                  'message': message})


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
            'kill_time': str(timezone.now() + relativedelta(hours=1)),
            'message': 'Download is being processed on the server',
            'status_code': None
        }
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)
        process_info_path = '{}/process_info.json'.format(ticket_path)
        write_file(process_info_path, process_info_obj, True)

        # Spawn job separate from request memory thread
        function_thread = multiprocessing.Process(target=download_resource, args=[
            target_name, action, token, resource_id, ticket_path, process_info_path])
        function_thread.start()

        # Get the download url
        reversed_url = reverse('download_resource', kwargs={
                               'ticket_number': ticket_number})
        download_hyperlink = request.build_absolute_uri(
            reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'download_link': download_hyperlink})


def download_resource(target_name, action, token, resource_id, ticket_path, process_info_path):
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
    """
    # Fetch the proper function to call
    func = FunctionRouter.get_function(target_name, action)

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
        data = read_file(process_info_path, True)
        data['status_code'] = e.status_code
        data['status'] = 'failed'
        data['message'] = e.data
        data['expiration'] = str(timezone.now() + relativedelta(hours=1))
        write_file(process_info_path, data, True)
        return

    # The directory all files should be saved in.
    file_name = '{}_download_{}'.format(target_name, resource_id)
    folder_directory = '{}/{}'.format(ticket_path, file_name)

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
        file_path = '{}{}'.format(folder_directory, resource['path'])
        write_file(file_path, resource['file'])

    # Add the fixity file to the disk directory
    file_path = '{}/fixity_info.json'.format(folder_directory)
    write_file(file_path, fixity_info, True)

    # Make a Bagit 'bag' of the resources.
    bagit.make_bag(folder_directory)

    # Zip the Bagit 'bag' to send forward.
    zip_file_path = "{}/{}.zip".format(ticket_path, file_name)
    zip_directory(zip_file_path, folder_directory)

    # Everything was a success so update the server metadata file.
    data = read_file(process_info_path, True)
    data['status_code'] = '200'
    data['status'] = 'finished'
    data['message'] = 'Download successful'
    write_file(process_info_path, data, True)
    return
