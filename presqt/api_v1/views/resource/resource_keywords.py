
import requests

from rest_framework.response import Response

from presqt.api_v1.utilities import (get_source_token, target_validation, FunctionRouter)
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.utilities import PresQTValidationError, PresQTResponseException


class ResourceKeywords(BaseResource):
    """
    **Supported HTTP Methods**

    * GET:
        - Retrieve a summary of all keywords of a given resource.
    * POST
        -  Upload new keywords to a given resource.
    """

    def get(self, request, target_name, resource_id):
        """
        Retrieve all keywords of a given resource.

        Parameters
        ----------
        target_name : str
            The string name of the Target resource to retrieve.
        resource_id : str
             The id of the Resource to retrieve.

        Returns
        -------
        200 : OK
        A dictionary containing the keywords of the resource.
        {
            "topics": [
                "eggs",
                "animal",
                "water"
            ],
            "keywords": [
                "eggs",
                "animal",
                "water"
            ]
        }

        400: Bad Request
        {
            "error": "{Target} {Resource Type} do not have keywords."
        }

        401: Unauthorized
        {
            "error": "Token is invalid. Response returned a 401 status code.""
        }
        """
        self.request = request
        self.source_target_name = target_name
        self.source_resource_id = resource_id
        self.action = 'keywords'

        try:
            token = get_source_token(self.request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(self.source_target_name, self.action)

        # Fetch the resource
        try:
            resource = func(token, self.source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        return Response(resource)

    def post(self, request, target_name, resource_id):
        """
        Upload suggested keywords to a given resource.

        Parameters
        ----------
        target_name : str
            The string name of the Target resource to retrieve.
        resource_id : str
             The id of the Resource to retrieve.

        Returns
        -------
        200 : OK
        A dictionary containing the keywords of the resource.
        {
            "updated_keywords": [
                "animal",
                "Animals",
                "aqua",
                "dihydrogen oxide",
                "DISORDERED SOLVENT",
                "EGG",
                "eggs",
                "Electrostatic Gravity Gradiometer",
                "oxidane",
                "OXYGEN ATOM",
                "Wasser",
                "water",
                "Water"
            ]
        }

        400: Bad Request
        {
            "error": "{Target} {Resource Type} do not have keywords."
        }

        401: Unauthorized
        {
            "error": "Token is invalid. Response returned a 401 status code.""
        }

        Target Error
        {
            "error": "{Target} returned a {status_code} error trying to update keywords.
        }
        """
        self.request = request
        self.source_target_name = target_name
        self.source_resource_id = resource_id

        try:
            token = get_source_token(self.request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(self.source_target_name, 'keywords')

        # Fetch the keywords
        try:
            keywords = func(token, self.source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        new_list_of_keywords = []
        # Get the new keyword suggestions from Sci-Graph
        for keyword in keywords['keywords']:
            new_list_of_keywords.append(keyword)
            response = requests.get(
                'http://ec-scigraph.sdsc.edu:9000/scigraph/vocabulary/term/{}?limit=20'.format(
                    keyword))
            if response.status_code != 200:
                continue
            for label in response.json()[0]['labels']:
                new_list_of_keywords.append(label)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(self.source_target_name, 'keywords_upload')

        try:
            updated_keywords = func(token, self.source_resource_id, new_list_of_keywords)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        return Response(updated_keywords)
