from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def api_root(request, format=None):
    """
    Overview of available resources in this API.
    """
    return Response({
        'presqt': "PresQT",
    })