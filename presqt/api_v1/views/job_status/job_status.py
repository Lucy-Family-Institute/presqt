from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from presqt.api_v1.utilities import get_source_token, get_process_info_data, hash_tokens
from presqt.utilities import PresQTValidationError


class JobStatus(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve the status of a job
    """
    def get(self, request, action):
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
        try:
            source_token = get_source_token(self.request)
            self.ticket_number = hash_tokens(source_token)
            self.process_data = get_process_info_data('jobs', self.ticket_number)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        try:
            func = getattr(self, action)
        except AttributeError:
            return Response(data={"error": "PresQT Error: {} is not a valid acton.".format(action)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return func()

    def collection(self):
        data = {
            'total_files': self.process_data['resource_collection']['total_files'],
            'files_finished': self.process_data['resource_collection']['files_finished']
        }
        return Response(status=status.HTTP_200_OK, data=data)