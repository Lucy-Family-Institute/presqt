from django.urls import path

from presqt.api_v1 import api_root
from presqt.api_v1.views.download.download_job import DownloadJob
from presqt.api_v1.views.resource.resource import Resource
from presqt.api_v1.views.resource.resource_collection import ResourceCollection
from presqt.api_v1.views.target.target import TargetCollection, Target
from presqt.api_v1.views.transfer.transfer_job import TransferJob
from presqt.api_v1.views.upload.upload_job import UploadJob

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
    path('targets/<str:target_name>/resources/<str:resource_id>/',
         Resource.as_view(), name="resource"),

    # Downloads
    path('downloads/<str:ticket_number>/', DownloadJob.as_view(), name='download_job'),

    # Uploads
    path('uploads/<str:ticket_number>/', UploadJob.as_view(), name='upload_job'),

    # Transfers
    path('transfers/<str:ticket_number>/', TransferJob.as_view(), name='transfer_job')
]