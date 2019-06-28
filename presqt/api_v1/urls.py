from django.urls import path

from presqt.api_v1 import api_root
from presqt.api_v1.views.resource.resource import Resource
from presqt.api_v1.views.resource.resource_collection import ResourceCollection
from presqt.api_v1.views.resource.resource_download import DownloadResource
from presqt.api_v1.views.target.target import TargetCollection, Target

api_v1_endpoints = [
    path('', api_root, name='api_root'),

    # Targets
    path('targets/', TargetCollection.as_view(), name="target_collection"),
    path('targets/<str:target_name>/', Target.as_view(), name="target"),

    # Resources
    path('targets/<str:target_name>/resources/',
         ResourceCollection.as_view(), name="resource_collection"),
    path('targets/<str:target_name>/resources/<str:resource_id>.<str:resource_format>/',
         Resource.as_view(), name="resource"),

    # Downloads
    path('downloads/<str:ticket_number>/',DownloadResource.as_view(), name='download_resource')
]