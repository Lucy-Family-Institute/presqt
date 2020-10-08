Service Endpoints
=================

Service Endpoints
-----------------

Service Collection
++++++++++++++++++

.. http:get:: /api_v1/services/

    Retrieve details of all ``Services``.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/services/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "name": "eaasi",
                "readable_name": "EaaSI",
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://presqt-prod.crc.nd.edu/api_v1/services/eaasi/",
                        "method": "GET"
                    }
                ]
            }
        ]

    :statuscode 200: ``Services successfully retrieved``

Service Details
+++++++++++++++

.. http:get:: /api_v1/services/(str: service_name)/

    Retrieve details of a single ``Service``.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/services/eaasi/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "name": "eaasi",
            "readable_name": "EaaSI",
            "links": [
                {
                    "name": "Proposals",
                    "link": "https://presqt-prod.crc.nd.edu/api_v1/services/eaasi/proposals/",
                    "method": "POST"
                }
            ]
        }

    :statuscode 200: ``Service`` successfully retrieved
    :statuscode 404: Invalid ``Service`` name

EaaSI Endpoints
---------------

Submit EaaSI Proposal
+++++++++++++++++++++

.. http:post:: /api_v1/services/eaasi/proposals/

    Send a file from a PresQT server to start a ``proposal task`` on an EaaSI server.

    **Example request**:

    .. sourcecode:: http

        POST /api_v1/services/eaasi/proposals/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

        Example body json:
            {
                "ticket_number":"39e56297-04cc-440a-b73e-9788b220f12b"
            }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": "19",
            "message": "Proposal task was submitted."
            "proposal_link": "https://presqt-prod.crc.nd.edu/api_v1/services/eaasi/1/"
        }

    :statuscode 200: Proposal successfully started.
    :statuscode 400: 'presqt-source-token' missing in request headers
    :statuscode 400: A download does not exist for this user on the server.
    :statuscode 404: Invalid ticket number
    :statuscode 404: A resource_download does not exist for this user on the server.


Get EaaSI Proposal
++++++++++++++++++

.. http:get:: /api_v1/services/eaasi/proposals/(str: proposal_id)/

    Check on the state of the EaaSI Proposal Task on the EaaSI server.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/services/eaasi/proposals/12/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response if the proposal task is not finished**:

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "message": "Proposal task is still in progress."
        }

    **Example response if the proposal task is finished successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "image_url": "https://eaasi-portal.emulation.cloud:443/blobstore/api/v1/blobs/imagebuilder-outputs/2ca330d6-23f7-4f0a-943a-e3984b29642c?access_token=default",
            "image_type": "cdrom",
            "environments": [],
            "suggested": {}
        }

    :statuscode 200: ``Proposal Task`` has finished successfully
    :statuscode 202: ``Proposal Task`` is being processed on the EaaSI server
    :statuscode 404: Invalid ``Proposal ID``

EaaSI Download
++++++++++++++

.. http:get:: /api_v1/services/eaasi/(str: ticket_number)/?eaasi_token=(str: eaasi_token)

    EaaSI specific download endpoint that exposes a resource on a PresQT server to download.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/services/eeasi/download/39e56297-04cc-440a-b73e/?eaasi=E9luKQU9Ywe5j HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/zip

        Payload is ZIP file

    :statuscode 200: File successfully retrieved.
    :statuscode 400: ``eaasi_token`` not found as query parameter.
    :statuscode 401: ``eaasi_token`` does not match the 'eaasi_token' for this server process.
    :statuscode 404: File unavailable.
    :statuscode 404: Invalid ticket number.
    :statuscode 404: A resource_download does not exist for this user on the server.


FAIRshare Endpoints
-------------------

Get FAIRshare Tests
+++++++++++++++++++

.. http:get:: /api_v1/services/fairshare/evaluator/

    Get a list of tests from FAIRshare that are currently supported by PresQT.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/services/fairshare/evaluator/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "test_name": "FAIR Metrics Gen2- Unique Identifier "
                "description": "Metric to test if the metadata resource has a unique identifier. This is done by comparing the GUID to the patterns (by regexp) of known GUID schemas such as URLs and DOIs. Known schema are registered in FAIRSharing (https://fairsharing.org/standards/?q=&selected_facets=type_exact:identifier%20schema)",
                "test_id": 1
            },
            {
                "test_name": "FAIR Metrics Gen2 - Identifier Persistence "
                "description": "Metric to test if the unique identifier of the metadata resource is likely to be persistent. Known schema are registered in FAIRSharing (https://fairsharing.org/standards/?q=&selected_facets=type_exact:identifier%20schema). For URLs that don't follow a schema in FAIRSharing we test known URL persistence schemas (purl, oclc, fdlp, purlz, w3id, ark).",
                "test_id": 2
            }...
        ]


    :statuscode 200: Tests returned successfully

POST FAIRshare Evaluator
++++++++++++++++++++++++

.. http:post:: /api_v1/services/fairshare/evaluator/

    Submit a FAIRshare Evaluation request with a doi and list of test ids.

    **Example request**:

    .. sourcecode:: http

        POST /api_v1/services/fairshare/evaluator/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

        Example body json:
            {
                "resource_id":"10.17605/OSF.IO/EGGS12",
                "tests": [1, 2]
            }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "metric_link": "https://w3id.org/FAIR_Evaluator/metrics/1",
                "test_name": "FAIR Metrics Gen2- Unique Identifier ",
                "description": "Metric to test if the metadata resource has a unique identifier. This is done by comparing the GUID to the patterns (by regexp) of known GUID schemas such as URLs and DOIs. Known schema are registered in FAIRSharing (https://fairsharing.org/standards/?q=&selected_facets=type_exact:identifier%20schema)",
                "successes": [
                    "Found an identifier of type 'doi'"
                ],
                "failures": [],
                "warnings": []
            },
            {
                "metric_link": "https://w3id.org/FAIR_Evaluator/metrics/2",
                "test_name": "FAIR Metrics Gen2 - Identifier Persistence ",
                "description": "Metric to test if the unique identifier of the metadata resource is likely to be persistent. Known schema are registered in FAIRSharing (https://fairsharing.org/standards/?q=&selected_facets=type_exact:identifier%20schema). For URLs that don't follow a schema in FAIRSharing we test known URL persistence schemas (purl, oclc, fdlp, purlz, w3id, ark).",
                "successes": [
                    "The GUID of the metadata is a doi, which is known to be persistent."
                ],
                "failures": [],
                "warnings": []
            }
        ]
    :statuscode 200: Evaluation completed successfully.
    :statuscode 400: 'resource_id' missing in the request body.
    :statuscode 400: 'tests' missing in the request body.
    :statuscode 400: 'tests' must be in list format.
    :statuscode 400: At least one test is required. Options are: [.......]
    :statuscode 400: 'eggs' not a valid test name. Options are: [.......]
    :statuscode 503: FAIRshare returned a <status_code> error trying to process the request