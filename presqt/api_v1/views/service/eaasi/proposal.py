import json
import requests

from rest_framework.views import APIView
from rest_framework.reverse import reverse


class Proposal(APIView):
    """
    Handles shared POST requests to EaaSI api.
    """

    def post(self, request, ticket_number=None):
        """
        Upload resources to an EaaSI node.

        Parameters
        ----------
        request : HTTP Request Object
        ticket_number : str
            The ticket number of the zip to pass along.
        """
        data = {
            "data_url": reverse('download_job', kwargs={
                'ticket_number': ticket_number, 'response_format': 'zip'}),
            "data_type": "bagit+zip"}

        response = requests.post(
            'https://eaasi-portal.emulation.cloud/environment-proposer/api/v1/proposals',
            data=json.dumps(data))
