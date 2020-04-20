from rest_framework.reverse import reverse
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def api_root(request, format=None):
    """
    Overview of available resources in this API.
    """
    return Response({
        'targets': reverse('target_collection', request=request, format=format),
        'statuses': reverse('status_collection', request=request, format=format),
        'services': reverse('service_collection', request=request, format=format),
    })
