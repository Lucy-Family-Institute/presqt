from uuid import uuid4

from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from presqt.api_v1.utilities import (
    get_source_token, target_validation, FunctionRouter, keyword_enhancer, get_target_data)
from presqt.utilities import PresQTValidationError, PresQTResponseException, PresQTError


class ResourceKeywords(APIView):
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
        action = 'keywords'

        try:
            token = get_source_token(request)
            target_validation(target_name, action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(target_name, action)

        # Fetch the resource keywords
        try:
            # Will return a dictionary with resource's keywords
            keywords = func(token, resource_id)
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
            "error": "PresQT Error: keywords is missing from the request body."
        }
        or
        {
            "error": "PresQT Error: keywords must be in list format."
        }

        401: Unauthorized
        {
            "error": "Token is invalid. Response returned a 401 status code.""
        }

        500: Internal Server Error
        {
            "error": "PresQT Error: Error updating the PresQT metadata file on {Target}. Keywords have been added successfully."
        }

        Target Error
        {
            "error": "{Target} returned a {status_code} error trying to update keywords.
        }
        """
        action = "keywords_upload"

        try:
            keywords = request.data['keywords']
        except KeyError:
            return Response(data={"error": "PresQT Error: keywords is missing from the request body."},
                            status=status.HTTP_400_BAD_REQUEST)

        if type(keywords) is not list:
            return Response(data={"error": "PresQT Error: keywords must be in list format."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            token = get_source_token(request)
            target_validation(target_name, action)
            target_validation(target_name, 'keywords')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the initial keyword function
        func = FunctionRouter.get_function(target_name, 'keywords')

        # Fetch the resource keywords
        try:
            # Will return a dictionary with resource's keywords
            initial_keywords = func(token, resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the update keywords function
        func = FunctionRouter.get_function(target_name, action)

        # Add the keywords
        all_keywords = initial_keywords['keywords'] + keywords

        # Function will upload new keywords to the selected resource
        try:
            # Will return a dictionary with the updated_keywords
            updated_keywords = func(token, resource_id, all_keywords)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        # Update the metadata file, or create a new one.
        metadata_func = FunctionRouter.get_function(target_name, 'metadata_upload')

        # Build the metadata dictionary for this action.
        source_target_data = get_target_data(target_name)

        metadata_dict = {
            "allEnhancedKeywords": updated_keywords['updated_keywords'],
            "actions": [{
                'id': str(uuid4()),
                'details': 'PresQT Enhance Keywords in {}'.format(source_target_data['readable_name']),
                'actionDateTime': str(timezone.now()),
                'actionType': 'keyword_enhancement',
                'sourceTargetName': target_name,
                'destinationTargetName': target_name,
                'sourceUsername': 'N/A',
                'destinationUsername': 'N/A',
                'keywordEnhancements': {
                    'initialKeywords': initial_keywords['keywords'],
                    'enhancedKeywords': updated_keywords['updated_keywords'],
                    'enhancer': 'scigraph'
                },
                'files': {
                    'created': [],
                    'updated': [],
                    'ignored': []
                }
            }]
        }

        try:
            metadata_func(token, updated_keywords['project_id'], metadata_dict)
        except PresQTError:
            # Catch any errors that happen within the target fetch
            return Response(
                data={'error': "PresQT Error: Error updating the PresQT metadata file on {}. Keywords have been added successfully.".format(
                    target_name)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(data={
            'initial_keywords': initial_keywords,
            'keywords_added': keywords,
            'final_keywords': updated_keywords['updated_keywords']},
            status=status.HTTP_202_ACCEPTED)
