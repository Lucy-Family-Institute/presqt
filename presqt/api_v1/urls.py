from django.urls import path

from presqt.api_v1 import api_root
from presqt.api_v1.views.target import TargetsList, TargetDetails

api_v1_endpoints = [
    path('', api_root),
    path('targets/', TargetsList.as_view(), name="targets_list"),
    path('target/<str:target_name>/', TargetDetails.as_view(), name="target_detail")
]