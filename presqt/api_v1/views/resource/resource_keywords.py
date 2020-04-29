
import requests

from rest_framework.response import Response

from presqt.api_v1.utilities import (get_source_token, target_validation, FunctionRouter)
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.utilities import PresQTValidationError, PresQTResponseException


class ResourceKeywords(BaseResource):
    """
    """

    def get(self, request, target_name, resource_id):
        """
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
        for keyword in keywords['keywords']:
            new_list_of_keywords.append(keyword)
            response = requests.get(
                'http://ec-scigraph.sdsc.edu:9000/scigraph/vocabulary/term/{}?limit=20'.format(
                    keyword))
            if response.status_code != 200:
                continue
            for label in response.json()[0]['labels']:
                new_list_of_keywords.append(label)

        # # Fetch the proper function to call
        # func = FunctionRouter.get_function(self.source_target_name, 'upload_keywords')

        # try:
        #     keywords = func(token, self.source_resource_id)
        # except PresQTResponseException as e:
        #     # Catch any errors that happen within the target fetch
        #     return Response(data={'error': e.data}, status=e.status_code)

        return Response({'keywords': new_list_of_keywords})
