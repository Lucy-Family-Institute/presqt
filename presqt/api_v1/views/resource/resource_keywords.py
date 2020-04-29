
from rest_framework.response import Response
from rest_framework import status

from presqt.api_v1.utilities import (
    get_source_token, target_validation, FunctionRouter, keyword_enhancer)
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
        or
        {
            "error": "PresQT Error: 'new_target' does not support the action 'resource_detail'."
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
            target_validation(self.source_target_name, self.action)
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

        return Response(data=resource, status=status.HTTP_200_OK)

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
        202 : ACCEPTED
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
        self.action = "keywords_upload"

        try:
            token = get_source_token(self.request)
            target_validation(self.source_target_name, 'keywords')
            target_validation(self.source_target_name, self.action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the initial keyword function
        func = FunctionRouter.get_function(self.source_target_name, 'keywords')

        # Fetch the keywords
        try:
            keywords = func(token, self.source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        new_list_of_keywords = keyword_enhancer(keywords)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(self.source_target_name, self.action)

        try:
            updated_keywords = func(token, self.source_resource_id, new_list_of_keywords)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        return Response(data=updated_keywords, status=status.HTTP_202_ACCEPTED)
