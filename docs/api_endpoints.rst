API Endpoints
=============

Authentication
--------------
Refer to the authentication details :doc:`here </authentication_authorization>`.

Duplicate File Handling
-----------------------
When ``Uploading`` or ``Transferring`` resources a header, ``presqt-file-duplicate-action``, must be
included. The options are ``ignore`` or ``update``. This header tells the target uploading the
resource what to do when a file being uploaded already exists in the source target.

``Ignore`` will not update the duplicate file, even if the contents of the files don't match.

``Update`` will only update the duplicate file if the contents of the files don't match.

Searching Resource Collections
------------------------------
Search results are ordered by date modified unless the target does not support it.

Only a single search filter can be used at a time.

Search Filters
++++++++++++++

General search across all available target search parameters: ``resources/?general=search_value``

Search by project 'title': ``resources/?title=Project+Title``

Search by project 'id': ``resources/?id=123456``

Search by project 'author': ``resources/?author=bfox6``

Search by project 'keywords': ``resources/?keywords=cat``

Paginating Resource Collections
-------------------------------

Pagination has been added at the collection level to improve load times. Targets now return Pagination
information for users resources, as well as searched resources.

Page Parameter
++++++++++++++

Pagination across all available targets: ``resources/?page=page_number``

Target Endpoints
----------------

Target Collection
+++++++++++++++++

.. http:get::  /api_v1/targets/

    Retrieve details of all ``Targets``.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "name": "osf",
                "readable_name": "OSF",
                "status_url": "https://api.osf.io/v2/nodes/",
                "supported_actions": {
                    "resource_collection": true,
                    "resource_detail": true,
                    "resource_download": true,
                    "resource_upload": true,
                    "resource_transfer_in": true,
                    "resource_transfer_out": true
                    "keywords": true,
                    "keywords_upload": true,
                },
                "supported_transfer_partners": {
                    "transfer_in": [
                        "github",
                        "curate_nd"
                    ],
                    "transfer_out": [
                        "github"
                    ]
                },
                "supported_hash_algorithms": [
                    "sha256",
                    "md5"
                ],
                "infinite_depth": true
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/",
                        "method": "GET"
                    }
                ]
            },
            {
                "name": "curate_nd",
                "readable_name": "CurateND",
                "status_url": "https://curate.nd.edu/api/items",
                "supported_actions": {
                    "resource_collection": true,
                    "resource_detail": true,
                    "resource_download": true,
                    "resource_upload": false,
                    "resource_transfer_in": false,
                    "resource_transfer_out": true,
                    "keywords": true,
                    "keywords_upload": false,
                },
                "supported_transfer_partners": {
                    "transfer_in": [],
                    "transfer_out": [
                        "osf",
                        "github"
                    ]
                },
                "supported_hash_algorithms": [
                    "md5"
                ],
                "infinite_depth": false
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/curate_nd/",
                        "method": "GET"
                    }
                ]
            }
        ]

    :statuscode 200: ``Targets`` successfully retrieved

Target Details
++++++++++++++

.. http:get::  /api_v1/targets/(str: target_name)/

    Retrieve details of a single ``Target``.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "name": "osf",
            "readable_name": "OSF",
            "status_url": "https://api.osf.io/v2/nodes/",
            "supported_actions": {
                "resource_collection": true,
                "resource_detail": true,
                "resource_download": true,
                "resource_upload": true,
                "resource_transfer_in": true,
                "resource_transfer_out": true,
                "keywords": true,
                "keywords_upload": true,
            },
            "supported_transfer_partners": {
                "transfer_in": [
                    "github",
                    "curate_nd"
                ],
                "transfer_out": [
                    "github"
                ]
            },
            "supported_hash_algorithms": [
                "sha256",
                "md5"
            ],
            "infinite_depth": true
            "links": [
                {
                    "name": "Collection",
                    "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/",
                    "method": "GET"
                },
                {
                    "name": "Upload",
                    "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/",
                    "method": "POST"
                },
                {
                    "name": "Transfer",
                    "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/",
                    "method": "POST"
                }
            ]
        }

    :statuscode 200: ``Target`` successfully retrieved
    :statuscode 404: Invalid ``Target`` name

Resource Endpoints
------------------

Resource Collection
+++++++++++++++++++

.. http:get::  /api_v1/targets/(str: target_name)/resources/

    Retrieve details of all top level resources for a given ``Target`` and ``User Token``

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "resources": [
                {
                    "kind": "container",
                    "kind_name": "project",
                    "id": "cmn5z",
                    "container": null,
                    "title": "Test Project",
                    "links": [
                        {
                            "name": "Detail",
                            "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/cmn5z/",
                            "method": "GET"
                        }
                    ]
                },
                {
                    "kind": "container",
                    "kind_name": "project",
                    "id": "12345",
                    "container": null,
                    "title": "Egg Project",
                    "links": [
                        {
                            "name": "Detail",
                            "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/12345/",
                            "method": "GET"
                        }
                    ]
                }
            ],
            "pages": {
                "first_page": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources?page=1",
                "previous_page": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources?page=5",
                "next_page": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources?page=7",
                "last_page": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources?page=30",
                "total_pages": 1,
                "per_page": 10,
                "base_page": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources?page="
            }
        }
    
    **Example request w/ search parameter**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources?title=egg/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json
    
    **Example request w/ search parameter and page parameter**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources?title=egg&page=3/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    Search filtering rules can be found here.

    :reqheader presqt-source-token: User's token for the source target
    :statuscode 200: ``Resources`` successfully retrieved
    :statuscode 400: The ``Target`` does not support the action ``resource_collection``
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 400: The ``search query`` is not formatted correctly.
    :statuscode 401: ``Token`` is invalid
    :statuscode 404: Invalid ``Target`` name

Resource Detail
+++++++++++++++

.. http:get::  /api_v1/targets/(str: target_name)/resources/(str: resource_id).json/

    Retrieve details of a ``Resource`` in JSON format

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources/1234.json/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "kind": "container",
            "kind_name": "project",
            "id": "cmn5z",
            "title": "Test Project",
            "date_created": "2019-05-13T15:06:34.521000Z",
            "date_modified": "2019-05-13T15:06:34.521000Z",
            "hashes": {
                "md5": null,
                "sha256": null
            },
            "extra": {
                "last_touched": "2019-11-07T17:00:51.680957",
                "materialized_path": "/Test Project",
                "current_version": 1,
                "provider": "googledrive",
                "path": "/Test Project",
                "current_user_can_comment": true,
                "guid": "byz93",
                "checkout": null,
                "tags": [],
                "size": null
            },
            "children": [
                {
                    "kind": "container",
                    "kind_name": "storage",
                    "id": "cmn5z:osfstorage",
                    "container": "cmn5z",
                    "title": "osfstorage",
                    "links": [
                        {
                            "name": "Detail",
                            "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/cmn5z:osfstorage/",
                            "method": "GET"
                        }
                    ]
                },
                {
                    "kind": "container",
                    "kind_name": "folder",
                    "id": "5cd9832cf244ec0021e5f245",
                    "container": "cmn5z:osfstorage",
                    "title": "Images",
                    "links": [
                        {
                            "name": "Detail",
                            "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/5cd9832cf244ec0021e5f245/",
                            "method": "GET"
                        }
                    ]
                },
                {
                    "kind": "item",
                    "kind_name": "file",
                    "id": "5cd98510f244ec001fe5632f",
                    "container": "5cd9832cf244ec0021e5f245",
                    "title": "22776439564_7edbed7e10_o.jpg",
                    "links": [
                        {
                            "name": "Detail",
                            "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/5cd98510f244ec001fe5632f/",
                            "method": "GET"
                        }
                    ]
                }
            ],
            "links": [
                {
                    "name": "Download",
                    "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/cmn5z.zip/",
                    "method": "GET"
                },
                {
                    "name": "Upload",
                    "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/cmn5z/",
                    "method": "POST"
                },
                {
                    "name": "Transfer",
                    "link": "https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/cmn5z/",
                    "method": "POST"
                }
            ],
            "actions": [
                "Transfer"
            ]
        }


    :reqheader presqt-source-token: User's token for the source target
    :statuscode 200: ``Resource`` successfully retrieved
    :statuscode 400: The ``Target`` does not support the action ``resource_detail``
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 400: Invalid format given. Must be ``json``
    :statuscode 401: ``Token`` is invalid
    :statuscode 403: User does not have access to this ``Resource``
    :statuscode 404: Invalid ``Target`` name
    :statuscode 404: ``Resource`` with this ``ID`` not found for this user
    :statuscode 410: ``Resource`` no longer available

Resource Download Endpoints
---------------------------

Download Resource
+++++++++++++++++

.. http:get::  /api_v1/targets/(str: target_name)/resources/(str: resource_id).zip/

    Retrieve a Resource as a ZIP file. This endpoint begins the download process but does not
    return the zip file. Rather, it returns a link which can be used to the hit the
    ``Job Status`` endpoint to check in on the process.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources/1234.zip/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "message": "The server is processing the request.",
            "download_job_zip": "https://presqt-prod.crc.nd.edu/api_v1/job_status/download.zip/",
            "download_job_json": "https://presqt-prod.crc.nd.edu/api_v1/job_status/download.json/"
        }

    :reqheader presqt-source-token: User's token for the source target
    :statuscode 202: ``Resource`` has begun downloading
    :statuscode 400: The ``Target`` does not support the action ``resource_download``
    :statuscode 400: User currently has processes in progress.
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 400: Invalid format given. Must be ``zip``
    :statuscode 404: Invalid ``Target`` name

Resource Download Job Status
++++++++++++++++++++++++++++

.. http:get:: /api_v1/job_status/download.json/

    Use the ``Job Status`` endpoint to check in on the ``Download Process``. Provide the
    ``presqt-source-token`` in the headers.

    **Example request**

    .. sourcecode:: http

        GET /api_v1/job_status/download/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response if the download request is still in progress**:

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "job_percentage": 27,
            "status": "in_progress",
            "status_code": null,
            "message": "Downloading files from OSF..."
        }

    **Example response if the download request finished successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status_code": "200",
            "message": "Download successful. See PRESQT_FTS_METADATA.json for more details.",
            "zip_name": "osf_download_cmn5z.zip",
            "failed_fixity": [
                "/Test Project/googledrive/PresQT Swimlane Activity Diagram 03_21_19 (2).pdf",
                "/Test Project/googledrive/module_responses.csv",
                "/Test Project/googledrive/Google Images/IMG_4740.jpg",
                "/Test Project/googledrive/Character Sheet - Alternative - Print Version.pdf"
            ],
            "job_percentage": 100,
            "status": "finished"
        }

    **Example response if the download failed**:

    .. sourcecode:: http

        HTTP/1.1 500 Internal Server Error
        Content-Type: application/json

        {
            "job_percentage": 0,
            "status": "failed",
            "status_code": 404,
            "message": "Resource with id 'bad_id' not found for this user."
        }

    :reqheader presqt-source-token: User's ``Token`` for the source target
    :statuscode 200: ``Download`` has finished successfully
    :statuscode 202: ``Download`` is being processed on the server
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 400: Invalid format given. Must be json or zip.
    :statuscode 404: Invalid ``Ticket Number``
    :statuscode 500: ``Download`` failed on the server

.. http:get:: /api_v1/job_status/download.zip/

    Check on the ``Download Process`` for the given user.
    If download has failed or is in progress this endpoint will return a JSON payload detailing this.
    If download has completed this endpoint will return the zip file of the resource originally requested.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/job_status/download.zip/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response if the download request is still in progress**:

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "job_percentage": 27,
            "status": "in_progress",
            "status_code": null,
            "message": "Downloading files from OSF..."
        }

    **Example response if download finished successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/zip

        Payload is ZIP file

    **Example response if the download failed**:

    .. sourcecode:: http

        HTTP/1.1 500 Internal Server Error
        Content-Type: application/json

        {
            "job_percentage": 0,
            "status": "failed",
            "status_code": 404,
            "message": "Resource with id 'bad_id' not found for this user."
        }

    :reqheader presqt-source-token: User's ``Token`` for the source target
    :statuscode 200: ``Download`` has finished successfully
    :statuscode 202: ``Download`` is being processed on the server
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 400: Invalid format given. Must be json or zip.
    :statuscode 404: Invalid ``Ticket Number``
    :statuscode 500: ``Download`` failed on the server

.. http:patch::  /api_v1/job_status/upload/

    Cancel the ``Download Process`` for the given user.`.

    If the download has finished before it can be cancelled it will return the finished info from process_info.json.

    If the download was successfully cancelled then it will return the cancelled info from process_info.json.

    **Example request**:

    .. sourcecode:: http

        PATCH /api_v1/job_status/download/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response if download cancelled successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status_code": "499",
            "message": "Download was cancelled by the user"
        }

    **Example response if download finished before endpoint was able to cancel**:

    .. sourcecode:: http

        HTTP/1.1 406 OK
        Content-Type: application/json

        {
            "status_code": "200",
            "message": "Download successful."
        }

    :reqheader presqt-source-token: User's ``Token`` for the source target
    :statuscode 200: ``Download`` cancelled
    :statuscode 406: ``Download`` finished before cancellation
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 404: Invalid ``Ticket Number``


Resource Upload Endpoints
---------------------------

Upload New Top Level Resource
+++++++++++++++++++++++++++++

.. http:post::  /api_v1/targets/(str: target_name)/resources/

    Upload a new top level resource, for instance a Project. This endpoint begins the ``Upload``
    process. It returns a link which can be used to the hit the ``Job Status`` endpoint to check
    in on the process.

    **Example request**:

    .. sourcecode:: http

        POST /api_v1/targets/OSF/resources/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    ..  sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "message": "The server is processing the request.",
            "upload_job": "https://presqt-prod.crc.nd.edu/api_v1/job_status/upload/"
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :reqheader presqt-file-duplicate-action: Action to be taken if a duplicate file is found (Either ``update`` or ``ignore``)
    :form presqt-file: The ``Resource`` to ``Upload``. Must be a BagIt file in ZIP format.
    :statuscode 202: ``Resource`` has begun uploading
    :statuscode 400: The ``Target`` does not support the action ``resource_upload``
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 400: The file, ``presqt-file``, is not found in the body of the request
    :statuscode 400: The file provided is not a zip file
    :statuscode 400: The file provided is not in BagIt format
    :statuscode 400: Checksums failed to validate
    :statuscode 400: ``presqt-file-duplicate-action`` missing in the request headers
    :statuscode 400: Invalid ``file_duplicate_action`` header give. The options are ``ignore`` or ``update``
    :statuscode 400: Repository is not formatted correctly. Multiple directories exist at the top level
    :statuscode 400: Repository is not formatted correctly. Files exist at the top level
    :statuscode 400: User currently has processes in progress.
    :statuscode 401: ``Token`` is invalid
    :statuscode 404: Invalid ``Target`` name

Upload To Existing Resource
+++++++++++++++++++++++++++

.. http:post::  /api_v1/targets/(str: target_name)/resources/(str: resource_id)/

    Upload a resource to an existing container. This endpoint begins the ``Upload``
    process. It returns a link which can be used to the hit the ``Job Status`` endpoint to check
    in on the process.

    **Example request**:

    .. sourcecode:: http

        POST /api_v1/targets/OSF/resources/1234/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    ..  sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "message": "The server is processing the request.",
            "upload_job": "https://presqt-prod.crc.nd.edu/api_v1/job_status/upload/"
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :reqheader presqt-file-duplicate-action: Action to be taken if a duplicate file is found (Either ``update`` or ``ignore``)
    :form presqt-file: The ``Resource`` to ``Upload``. Must be a BagIt file in ZIP format.
    :statuscode 202: ``Resource`` has begun uploading
    :statuscode 400: The ``Target`` does not support the action ``resource_upload``
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 400: The file, ``presqt-file``, is not found in the body of the request
    :statuscode 400: The file provided is not a zip file
    :statuscode 400: The file provided is not in BagIt format
    :statuscode 400: Checksums failed to validate
    :statuscode 400: ``presqt-file-duplicate-action`` missing in the request headers
    :statuscode 400: Invalid ``file_duplicate_action`` header give. The options are ``ignore`` or ``update``
    :statuscode 400: User currently has processes in progress.
    :statuscode 401: ``Token`` is invalid
    :statuscode 403: User does not have access to this ``Resource``
    :statuscode 404: Invalid ``Target`` name
    :statuscode 410: ``Resource`` no longer available

Resource Upload Job Status
++++++++++++++++++++++++++

.. http:get::  /api_v1/job_status/upload/

    Check on the ``Upload Process`` for the given user.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/job_status/upload/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response if the upload is in progress**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status_code": null,
            "message": "Uploading files to OSF...",
            "status": "in_progress",
            "job_percentage": 0
        }

    **Example response if upload finished successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status_code": "200",
            "message": "Upload successful.",
            "status": "finished",
            "failed_fixity": [],
            "resources_ignored": [],
            "resources_updated": [],
            "job_percentage": 99
        }

    **Example response if upload failed**:

    .. sourcecode:: http

        HTTP/1.1 500 Internal Server Error
        Content-Type: application/json

        {
            "job_percentage": 0,
            "status": "failed",
            "status_code": 404,
            "message": "Resource with id 'bad_id' not found for this user."
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :statuscode 200: ``Upload`` has finished successfully
    :statuscode 202: ``Upload`` is being processed on the server
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 404: Invalid ``Ticket Number``
    :statuscode 500: ``Upload`` failed on the server

.. http:patch::  /api_v1/job_status/upload/

    Cancel the ``Upload Process`` for the given user.
    If the upload has finished before it can be cancelled it will return the finished info from process_info.json.
    If the upload was successfully cancelled then it will return the cancelled info from process_info.json.

    **Example request**:

    .. sourcecode:: http

        PATCH /api_v1/job_status/upload/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response if upload cancelled successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status_code": "499",
            "message": "Upload was cancelled by the user"
        }

    **Example response if upload finished before endpoint was able to cancel**:

    .. sourcecode:: http

        HTTP/1.1 406 OK
        Content-Type: application/json

        {
            "status_code": "200",
            "message": "Upload successful."
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :statuscode 200: ``Upload`` cancelled
    :statuscode 406: ``Upload`` finished before cancellation
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 404: Invalid ``Ticket Number``


Resource Transfer Endpoints
---------------------------

.. Note::

    The Upload and Transfer endpoints are the same POST endpoints **except**
    the specification of where the source resource is coming from.

    For ``Uploads`` the resource will be a file provided as form-data

    For ``Transfers`` the location of resource (source_target and resource_id) will be specified in the body as JSON

Transfer New Top Level Resource
+++++++++++++++++++++++++++++++

.. http:post::  /api_v1/targets/(str: target_name)/resources/

    Transfer a resource from a source target to a destination target. Make the resource a new
    top level resource, for instance a Project. This endpoint begins the ``Transfer``
    process. It returns a link which can be used to the hit the ``Job Status`` endpoint to check
    in on the process.

    **Example request**:

    .. sourcecode:: http

        POST /api_v1/targets/OSF/resources/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

        Example body json:
            {
                "source_target_name":"github",
                "source_resource_id": "209372336",
                "keywords": ["keywords", "to", "add"]
            }

    **Example response**:

    ..  sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "message": "The server is processing the request.",
            "transfer_job": "https://presqt-prod.crc.nd.edu/api_v1/job_status/transfer/"
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :reqheader presqt-source-token: User's ``Token`` for the source target
    :reqheader presqt-file-duplicate-action: Action to be taken if a duplicate file is found (Either ``update`` or ``ignore``)
    :reqheader presqt-keyword-action: Type of keyword action to perform (Either ``automatic`` or ``manual``)
    :jsonparam string source_target_name: The ``Source Target`` where the ``Resource`` being ``Transferred`` exists
    :jsonparam string source_resource_id: The ID of the ``Resource`` to ``Transfer``
    :statuscode 202: ``Resource`` has begun transferring
    :statuscode 400: The ``Source Target`` does not support the action ``resource_transfer_out``
    :statuscode 400: The ``Destination Target`` does not support the action ``resource_transfer_in``
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 400: ``presqt-file-duplicate-action`` missing in the request headers
    :statuscode 400: Invalid ``file-duplicate-action`` header give. The options are ``ignore`` or ``update``
    :statuscode 400: ``source_resource_id`` can't be none or blank
    :statuscode 400: ``source_resource_id`` was not found in the request body
    :statuscode 400: ``source_target_name`` was not found in the request body
    :statuscode 400: ``keywords`` was not found in the request body.
    :statuscode 400: ``keywords`` must be in list format.
    :statuscode 400: Source target does not allow transfer to the destination target
    :statuscode 400: Destination target does not allow transfer to the source target
    :statuscode 400: Invalid ``presqt-keyword-action`` header given. The options are ``automatic`` or ``manual``
    :statuscode 400: ``presqt-keyword-action`` missing in the request headers
    :statuscode 400: User currently has processes in progress.
    :statuscode 401: ``Source Token`` is invalid
    :statuscode 401: ``Destination Token`` is invalid
    :statuscode 403: User does not have access to the ``Resource`` to transfer
    :statuscode 404: Invalid ``Source Target`` name
    :statuscode 404: Invalid ``Destination Target`` name
    :statuscode 410: ``Resource`` to transfer is no longer available

Transfer To Existing Resource
+++++++++++++++++++++++++++++

.. http:post::  /api_v1/targets/(str: target_name)/resources/(str: resource_id)/

    Transfer a resource from a source target to a destination target. Transfer to an existing resource.
    This endpoint begins the ``Transfer`` process. It returns a link which can be used to
    the hit the ``Job Status`` endpoint to check in on the process.

     **Example request**:

    .. sourcecode:: http

        POST /api_v1/targets/OSF/resources/1234/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

        Example body json:
            {
                "source_target_name":"github",
                "source_resource_id": "209372336",
                "keywords": ["keywords", "to", "add"]
            }

    **Example response**:

    ..  sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "message": "The server is processing the request.",
            "transfer_job": "https://presqt-prod.crc.nd.edu/api_v1/job_status/transfer/"
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :reqheader presqt-source-token: User's ``Token`` for the source target
    :reqheader presqt-file-duplicate-action: Action to be taken if a duplicate file is found (Either ``update`` or ``ignore``)
    :reqheader presqt-keyword-action: Type of keyword action to perform (Either ``automatic`` or ``manual``)
    :jsonparam string source_target_name: The ``Source Target`` where the ``Resource`` being ``Transferred`` exists
    :jsonparam string source_resource_id: The ID of the ``Resource`` to ``Transfer``
    :statuscode 202: ``Resource`` has begun transferring
    :statuscode 400: The ``Source Target`` does not support the action ``resource_transfer_out``
    :statuscode 400: The ``Destination Target`` does not support the action ``resource_transfer_in``
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 400: ``presqt-file-duplicate-action`` missing in the request headers
    :statuscode 400: Invalid ``file_duplicate_action`` header give. The options are ``ignore`` or ``update``
    :statuscode 400: ``source_resource_id`` can't be none or blank
    :statuscode 400: ``source_resource_id`` was not found in the request body
    :statuscode 400: ``source_target_name`` was not found in the request body
    :statuscode 400: ``keywords`` was not found in the request body.
    :statuscode 400: ``keywords`` must be in list format.
    :statuscode 400: Source target does not allow transfer to the destination target
    :statuscode 400: Destination target does not allow transfer to the source target
    :statuscode 400: Invalid ``presqt-keyword-action`` header given. The options are ``automatic`` or ``manual``
    :statuscode 400: ``presqt-keyword-action`` missing in the request headers
    :statuscode 400: User currently has processes in progress.
    :statuscode 401: ``Source Token`` is invalid
    :statuscode 401: ``Destination Token`` is invalid
    :statuscode 403: User does not have access to the ``Resource`` to transfer
    :statuscode 403: User does not have access to the ``Resource`` to transfer to
    :statuscode 404: Invalid ``Source Target`` name
    :statuscode 404: Invalid ``Destination Target`` name
    :statuscode 410: ``Resource`` to transfer is no longer available
    :statuscode 410: ``Resource`` to transfer to is longer available


Resource Transfer Job Status
++++++++++++++++++++++++++++

.. http:get::  /api_v1/job_status/transfer/

    Check on the ``Transfer Process`` for the given user.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/job_status/transfer/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response if transfer is in progress**:

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "status_code": null,
            "message": "Creating PRESQT_FTS_METADATA...",
            "job_percentage": 50
        }

    **Example response if transfer finished successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status_code": "200",
            "message": "Transfer successful.",
            "job_percentage": 99,
            "failed_fixity": [
                "/PrivateProject/README.md"
            ],
            "resources_ignored": [],
            "resources_updated": [],
            "enhanced_keywords": [
                "EGG",
                "DISORDERED SOLVENT",
                "Electrostatic Gravity Gradiometer",
                "animal house",
                "aqua",
                "Wasser",
            ],
            "initial_keywords": [
                "animals",
                "eggs",
                "water"
            ],
            "source_resource_id": "209372336",
            "destination_resource_id": "qadt3"
        }

    **Example response if transfer failed**:

    .. sourcecode:: http

        HTTP/1.1 500 Internal Server Error
        Content-Type: application/json

        {
            "status_code": 404,
            "message": "The resource with id, 20938989898989872336, does not exist for this user.",
            "job_percentage": 0,
            "status": "failed"
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :reqheader presqt-source-token: User's ``Token`` for the source target
    :statuscode 200: ``Transfer`` has finished successfully
    :statuscode 202: ``Transfer`` is being processed on the server
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 404: Invalid ``Ticket Number``
    :statuscode 500: ``Transfer`` failed on the server

.. http:patch::  /api_v1/job_status/transfer/

    Cancel the ``Transfer Process`` for the given user.
    If the transfer has finished before it can be cancelled it will return the finished info from process_info.json.
    If the transfer was successfully cancelled then it will return the cancelled info from process_info.json.

    **Example request**:

    .. sourcecode:: http

        PATCH /api_v1/job_status/transfer/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response if transfer cancelled successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status_code": "499",
            "message": "Transfer was cancelled by the user"
        }

    **Example response if transfer finished before endpoint was able to cancel**:

    .. sourcecode:: http

        HTTP/1.1 406 OK
        Content-Type: application/json

        {
            "status_code": "200",
            "message": "Transfer successful."
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :reqheader presqt-source-token: User's ``Token`` for the source target
    :statuscode 200: ``Transfer`` cancelled
    :statuscode 406: ``Transfer`` finished before cancellation
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 404: Invalid ``Ticket Number``


Keyword Enhancement Endpoints
-----------------------------

Get a Resource's Keywords And Keyword Enhancements
++++++++++++++++++++++++++++++++++++++++++++++++++

.. http:get:: /api_v1/targets/(str: target_name)/resources/(str: resource_id)/keywords/

    Retrieve a resource's keywords that are both stored in the target and in the PresQT Metadata File (if one exists).
    Send the keywords to a keyword enhancer. Return both the ``Target Keywords`` and ``Enhanced Keywords`` in the payload.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources/1234/keywords/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "keywords": [
                "eggs",
                "animal",
                "water"
            ],
            "enhanced_keywords": [
                "animals",
                "Animals",
                "EGG",
                "Electrostatic Gravity Gradiometer",
                "water",
                "Water",
                "DISORDERED SOLVENT",
                "aqua",
                "Wasser",
                "dihydrogen oxide",
                "OXYGEN ATOM",
                "oxidane",
            ],
            "all_keywords": [
                "animals",
                "Animals",
                "EGG",
                "Electrostatic Gravity Gradiometer",
                "water",
                "Water",
                "DISORDERED SOLVENT",
                "aqua",
                "Wasser",
                "dihydrogen oxide",
                "OXYGEN ATOM",
                "oxidane",
                "eggs",
                "animal",
                "water"
            ]
        }

    :reqheader presqt-source-token: User's ``Token`` for the source target
    :statuscode 200: Keywords successfully fetched
    :statuscode 400: The ``Source Target`` does not support the action ``keywords``
    :statuscode 400: The ``resource type`` does not support ``keywords``
    :statuscode 401: ``Source Token`` is invalid

Upload Keywords to a Resource
+++++++++++++++++++++++++++++

.. http:post:: /api_v1/targets/(str: target_name)/resources/(str: resource_id)/keywords/

    Take a list of keywords and add them to the Resource's keywords both in the target and in
    the PresQT FTS Metadata file. The returned payload will contain both the new keywords added
    and the final full list of keywords in the target.

    **Example request**:

    .. sourcecode:: http

        POST /api_v1/targets/OSF/resources/1234/keywords/ HTTP/1.1
        Host: presqt-prod.crc.nd.edu
        Accept: application/json

        Example body json:
            {
                "keywords": ["cat", "water"]
            }

    **Example response**:

    ..  sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "keywords_added": [
                "feline",
                "aqua",
                "dihydrogen oxide",
                "DISORDERED SOLVENT",
                "EGG",
                "Electrostatic Gravity Gradiometer",
                "oxidane",
                "OXYGEN ATOM",
                "Wasser",
                "Water"
            ],
            "final_keywords": [
                "feline",
                "aqua",
                "dihydrogen oxide",
                "DISORDERED SOLVENT",
                "EGG",
                "eggs",
                "Electrostatic Gravity Gradiometer",
                "oxidane",
                "OXYGEN ATOM",
                "Wasser",
                "water",
                "Water"
            ]
        }

    :reqheader presqt-source-token: User's ``Token`` for the source target
    :jsonparam array keywords: An array of the ``keywords`` to upload
    :statuscode 202: ``Keywords successfully uploaded``
    :statuscode 400: The ``Source Target`` does not support the action ``keywords``
    :statuscode 400: The ``Source Target`` does not support the action ``keywords_upload``
    :statuscode 400: The ``resource type`` does not support ``keywords``
    :statuscode 400: ``keywords`` is missing from the request body
    :statuscode 400: ``keywords`` must be in list format
    :statuscode 401: ``Source Token`` is invalid

