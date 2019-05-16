from django.urls import path

from presqt.api_v1 import api_root
from presqt.api_v1.views.resource import ResourceCollection, Resource, ResourceDownload
from presqt.api_v1.views.target import TargetCollection, Target

api_v1_endpoints = [
    path('', api_root, name='api_root'),

    # Targets
    path('targets/', TargetCollection.as_view(), name="target_collection"),
    path('targets/<str:target_name>/', Target.as_view(), name="target"),

    # Resources
    path('targets/<str:target_name>/resources/',
         ResourceCollection.as_view(), name="resource_collection"),
    path('targets/<str:target_name>/resources/<str:resource_id>/',
         Resource.as_view(), name="resource"),
    # Resource Transfer
    path('targets/<str:target_name>/resources/<str:resource_id>/download/',
         ResourceDownload.as_view(), name="resource_download")
]