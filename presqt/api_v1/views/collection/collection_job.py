from rest_framework import status
from rest_framework.views import APIView

from presqt.api_v1.utilities import (get_source_token, process_token_validation, hash_tokens,
                                     get_process_info_data)
from presqt.utilities import PresQTValidationError
from rest_framework.response import Response


class CollectionJob(APIView):
    """
    **Supported HTTP Methods**

    * GET:
        - Check if a given resource's collection is finished.
    """

    def get(self, request, ticket_number):
        """
        Check in on the resource's collection process state.

        Parameters
        ----------
        ticket_number : str
            The ticket number of the collection being prepared.

        Returns
        -------
        200: OK
        {
            "presqt-source-token": "8f9335e63ff38a13f7977d20b6df637c1cdaf9eec6df7cf6b432e80df8b83c",
            "total_files": 3,
            "files_finished": 3
        }

        400: Bad Request
        {
            "error": "PresQT Error: 'presqt-source-token' missing in the request headers."
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

        """
        # Perform token validation. Read data from the process_info file.
        try:
            token = get_source_token(request)
            process_data = get_process_info_data('collection', ticket_number)
            process_token_validation(hash_tokens(token), process_data, 'presqt-source-token')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        data = {'total_files': process_data['total_files'], 'files_finished': process_data['files_finished']}
        return Response(status=status.HTTP_200_OK, data=data)