import requests

from rest_framework import renderers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import UserAuthentication
from presqt.api_v1.utilities.validation.target_validation import simple_target_validation
from presqt.api_v1.utilities.validation.token_validation import get_auth_token
from presqt.api_v1.utilities.validation.auth_body_validation import auth_body_validation
from presqt.utilities import PresQTValidationError


class TargetAuthenticate(APIView):
    renderer_classes = [renderers.JSONRenderer]

    def post(self, request, target):
        # Validate target
        # Validate auth_token in request
        # Validate request body
        # Body should be {'authorization': <token>}
        try:
            auth_token = get_auth_token(request)
            target_name = simple_target_validation(target)
            authorization = auth_body_validation(request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)
        # Validate user's auth token
        try:
            auth_user = UserAuthentication.objects.get(auth_token=auth_token)
        except UserAuthentication.DoesNotExist:
            return Response(data={'error': 'No user found with provided auth token.'}, status=status.HTTP_400_BAD_REQUEST)

        # Post users token for target to appropriate field in model
        setattr(auth_user, "{}_token".format(target_name), authorization)
        auth_user.save()

        return Response(data={'message': 'Token successfully added to auth_user'}, status=status.HTTP_200_OK)
