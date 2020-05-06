
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
            "keywords": [
                "eggs",
                "animal",
                "water"
            ],
            "enhanced_keywords": [
                "animals",
                "Animals",
                "eggs",
                "EGG",
                "Electrostatic Gravity Gradiometer",
                "water",
                "Water",
                "DISORDERED SOLVENT",
                "aqua",
                "Wasser",
                "dihydrogen oxide",
                "OXYGEN ATOM",
                "oxidane",
                "water"
            ]
        }

        400: Bad Request
        {
            "error": "{Target} {Resource Type} do not have keywords."
        }
        or
        {
            "error": "PresQT Error: 'new_target' does not support the action 'keywords'."
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

        # Fetch the resource keywords
        try:
            # Will return a dictionary with resource's keywords
            keywords = func(token, self.source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen
            return Response(data={'error': e.data}, status=e.status_code)

        # Call function which calls SciGraph for keyword suggestions.
        try:
            # Return a new keyword list and a final list.
            new_list_of_keywords, final_list_of_keywords = keyword_enhancer(keywords['keywords'])
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        return Response(data={
            "keywords": keywords['keywords'],
            "enhanced_keywords": final_list_of_keywords},
            status=status.HTTP_200_OK)

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
            "keywords_added": [
                "Animals",
                "aqua",
                "dihydrogen oxide",
                "DISORDERED SOLVENT",
                "EGG",
                "Electrostatic Gravity Gradiometer",
                "oxidane",
                "OXYGEN ATOM",
                "Wasser",
                "Water"
            ],
            "final_keywords": [
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
        or
        {
            "error": "PresQT Error: 'new_target' does not support the action 'keywords'."
        }
        or
        {
            "error": "PresQT Error: 'new_target' does not support the action 'keywords_upload'."
        }
        or
        {
            "error": "keywords is missing from the request body."
        }
        or
        {
            "error": "keywords must be in list format."
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
            keywords = request.data['keywords']
        except KeyError:
            return Response(data={"error": "keywords is missing from the request body."},
                            status=status.HTTP_400_BAD_REQUEST)

        if type(keywords) is not list:
            return Response(data={"error": "keywords must be in list format."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            token = get_source_token(self.request)
            target_validation(self.source_target_name, self.action)
            target_validation(self.source_target_name, 'keywords')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the initial keyword function
        func = FunctionRouter.get_function(self.source_target_name, 'keywords')

        # Fetch the resource keywords
        try:
            # Will return a dictionary with resource's keywords
            initial_keywords = func(token, self.source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the update keywords functtion
        func = FunctionRouter.get_function(self.source_target_name, self.action)

        # Add the keywords
        all_keywords = initial_keywords['keywords'] + keywords

        # Function will upload new keywords to the selected resource
        try:
            # Will return a dictionary with the updated_keywords
            updated_keywords = func(token, self.source_resource_id, all_keywords)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        return Response(data={
            'keywords_added': keywords,
            'final_keywords': updated_keywords['updated_keywords']},
            status=status.HTTP_202_ACCEPTED)
