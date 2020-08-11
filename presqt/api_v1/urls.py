from django.urls import path

from presqt.api_v1.views.job_status.job_status import JobStatus
from presqt.api_v1.views.bag_and_zip.bag_and_zip import BagAndZip
from presqt.api_v1.views.status.status import StatusCollection
from presqt.api_v1 import api_root
from presqt.api_v1.views.resource.resource import Resource
from presqt.api_v1.views.resource.resource_keywords import ResourceKeywords
from presqt.api_v1.views.resource.resource_collection import ResourceCollection
from presqt.api_v1.views.service.eaasi.proposal import Proposals, Proposal
from presqt.api_v1.views.target.target import TargetCollection, Target
from presqt.api_v1.views.service.service import ServiceCollection, Service
from presqt.api_v1.views.service.eaasi.download import EaasiDownload
from presqt.api_v1.views.transfer.transfer_job import TransferJob

api_v1_endpoints = [
    path('', api_root, name='api_root'),

    # Targets
    path('targets/', TargetCollection.as_view(), name="target_collection"),
    path('targets/<str:target_name>/', Target.as_view(), name="target"),

    # Statuses
    path('statuses/', StatusCollection.as_view(), name="status_collection"),

    # Resources
    path('targets/<str:target_name>/resources/',
         ResourceCollection.as_view(), name="resource_collection"),
    path('targets/<str:target_name>/resources/<str:resource_id>.<str:resource_format>/',
         Resource.as_view(), name="resource"),
    path('targets/<str:target_name>/resources/<str:resource_id>/',
         Resource.as_view(), name="resource"),
    path('targets/<str:target_name>/resources/<str:resource_id>/keywords/',
         ResourceKeywords.as_view(), name="keywords"),

    # Transfers
    path('transfers/<str:ticket_number>/', TransferJob.as_view(), name='transfer_job'),

    # Services
    path('services/', ServiceCollection.as_view(), name='service_collection'),
    path('services/<str:service_name>/', Service.as_view(), name='service'),

    # EaaSI specific
    path('services/eaasi/proposals/', Proposals.as_view(), name='proposals'),
    path('services/eaasi/proposals/<str:proposal_id>/', Proposal.as_view(), name='proposal'),
    path('services/eaasi/download/<str:ticket_number>/', EaasiDownload.as_view(), name='eaasi_download'),

    # BagIt and Zip Tool
    path('bag_and_zip/', BagAndZip.as_view(), name='bag_and_zip'),

    # Job Status
    path('job_status/<str:action>.<str:response_format>/', JobStatus.as_view(), name='job_status'),
    path('job_status/<str:action>/', JobStatus.as_view(), name='job_status')
]
