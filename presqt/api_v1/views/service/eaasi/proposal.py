import json
import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status


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
            "data_url": "https://presqt.readthedocs.io/en/latest/_downloads/cca126b15be422e27bfe28e0b7f994db/NewProjectWithFolderBagIt.zip",
            "data_type": "bagit+zip"}

        response = requests.post(
            'https://eaasi-portal.emulation.cloud/environment-proposer/api/v1/proposals',
            data=json.dumps(data),
            headers={"Content-Type": "application/json"})
        
        return Response(
                data=response.json(),
                status=status.HTTP_202_ACCEPTED)
