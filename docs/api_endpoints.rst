API Endpoints
=============

Authentication
--------------
Refer to the authentication details :doc:`here </authentication_authorization>`.


Target Endpoints
----------------

Target Collection
+++++++++++++++++

.. http:get::  /api_v1/targets/

    Retrieve details of all ``Targets``.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/ HTTP/1.1
        Host: localhost
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "name": "osf",
                "readable_name": "OSF",
                "supported_actions": {
                    "resource_collection": true,
                    "resource_detail": true,
                    "resource_download": true,
                    "resource_upload": true,
                    "resource_transfer_in": true,
                    "resource_transfer_out": true
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
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/targets/osf/",
                        "method": "GET"
                    }
                ]
            },
            {
                "name": "curate_nd",
                "readable_name": "CurateND",
                "supported_actions": {
                    "resource_collection": true,
                    "resource_detail": true,
                    "resource_download": true,
                    "resource_upload": false,
                    "resource_transfer_in": false,
                    "resource_transfer_out": true
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
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/targets/curate_nd/",
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
        Host: localhost
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "name": "osf",
            "readable_name": "OSF",
            "supported_actions": {
                "resource_collection": true,
                "resource_detail": true,
                "resource_download": true,
                "resource_upload": true,
                "resource_transfer_in": true,
                "resource_transfer_out": true
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
            "links": [
                {
                    "name": "Collection",
                    "link": "https://localhost/api_v1/targets/osf/resources/",
                    "method": "GET"
                },
                {
                    "name": "Upload",
                    "link": "https://localhost/api_v1/targets/osf/resources/",
                    "method": "POST"
                },
                {
                    "name": "Transfer",
                    "link": "https://localhost/api_v1/targets/osf/resources/",
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

    Retrieve details of all resources for a given ``Target`` and ``User Token``

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources/ HTTP/1.1
        Host: localhost
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "kind": "container",
                "kind_name": "project",
                "id": "cmn5z",
                "container": null,
                "title": "Test Project",
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/targets/osf/resources/cmn5z/",
                        "method": "GET"
                    }
                ]
            },
            {
                "kind": "container",
                "kind_name": "storage",
                "id": "cmn5z:osfstorage",
                "container": "cmn5z",
                "title": "osfstorage",
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/targets/osf/resources/cmn5z:osfstorage/",
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
                        "link": "https://localhost/api_v1/targets/osf/resources/5cd9832cf244ec0021e5f245/",
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
                        "link": "https://localhost/api_v1/targets/osf/resources/5cd98510f244ec001fe5632f/",
                        "method": "GET"
                    }
                ]
            }
        ]

    :reqheader presqt-source-token: User's token for the source target
    :statuscode 200: ``Resources`` successfully retrieved
    :statuscode 400: The ``Target`` does not support the action ``resource_collection``
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 401: ``Token`` is invalid
    :statuscode 404: Invalid ``Target`` name

Resource Detail
+++++++++++++++

.. http:get::  /api_v1/targets/(str: target_name)/resources/(str: resource_id).json/

    Retrieve details of a ``Resource`` in JSON format

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources/1234.json/ HTTP/1.1
        Host: localhost
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "kind": "item",
            "kind_name": "file",
            "id": "5cd98a30f2c01100177156be",
            "title": "Character Sheet - Alternative - Print Version.pdf",
            "date_created": "2019-05-13T15:06:34.521000Z",
            "date_modified": "2019-05-13T15:06:34.521000Z",
            "hashes": {
                "md5": null,
                "sha256": null
            },
            "extra": {
                "last_touched": "2019-11-07T17:00:51.680957",
                "materialized_path": "/Character Sheet - Alternative - Print Version.pdf",
                "current_version": 1,
                "provider": "googledrive",
                "path": "/Character%20Sheet%20-%20Alternative%20-%20Print%20Version.pdf",
                "current_user_can_comment": true,
                "guid": "byz93",
                "checkout": null,
                "tags": [],
                "size": null
            },
            "links": [
                {
                    "name": "Download",
                    "link": "https://localhost/api_v1/targets/osf/resources/5cd98a30f2c01100177156be.zip/",
                    "method": "GET"
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
    return the zip file. Rather, it returns a ``ticket_number`` which can be passed to the
    ``Download Job`` endpoint to check in on the process.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/targets/OSF/resources/1234.zip/ HTTP/1.1
        Host: localhost
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "ticket_number": "75963741-8d7f-4278-ae3e-2c2544caa631",
            "message": "The server is processing the request.",
            "download_job": "https://localhost/api_v1/downloads/75963741-8d7f-4278-ae3e-2c2544caa631/"
        }

    :reqheader presqt-source-token: User's token for the source target
    :statuscode 202: ``Resource`` has begun downloading
    :statuscode 400: The ``Target`` does not support the action ``resource_download``
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 400: Invalid format given. Must be ``zip``
    :statuscode 404: Invalid ``Target`` name


Download Job
++++++++++++

.. http:get::  /api_v1/download/(str: ticket_number)/

    Check on the ``Download Process`` for the given ``ticket_number``.
    If download has failed or is in progress this endpoint will return a JSON payload detailing this.
    If download has completed this endpoint will return the zip file of the resource originally requested.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/download/c24442a7-fead-4fb8-b56e-d4196ad55482/ HTTP/1.1
        Host: localhost
        Accept: application/json

    **Example response if download finished successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/zip

        Payload is ZIP file

    **Example response if download is in progress**:

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "status_code": null,
            "message": "Download is being processed on the server"
        }

    **Example response if download failed**:

    .. sourcecode:: http

        HTTP/1.1 500 Internal Server Error
        Content-Type: application/json

        {
            "status_code": "404",
            "message": "Resource with id 'bad_id' not found for this user."
        }

    :reqheader presqt-source-token: User's ``Token`` for the source target
    :statuscode 200: ``Download`` has finished successfully
    :statuscode 202: ``Download`` is being processed on the server
    :statuscode 400: ``presqt-source-token`` missing in the request headers
    :statuscode 401: Header ``presqt-source-token`` does not match the ``presqt-source-token`` for this server process
    :statuscode 404: Invalid ``Ticket Number``
    :statuscode 500: Download failed on the server

Resource Upload Endpoints
---------------------------

Upload New Top Level Resource
+++++++++++++++++++++++++++++

.. http:post::  /api_v1/targets/(str: target_name)/resources/

    Upload a new top level resource, for instance a Project. This endpoint begins the ``Upload``
    process. It returns a ``ticket_number`` which can be passed to the ``Upload Job`` endpoint to
    check in on the process.

    **Example request**:

    .. sourcecode:: http

        POST /api_v1/targets/OSF/resources/ HTTP/1.1
        Host: localhost
        Accept: application/json

    **Example response**:

    ..  sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "ticket_number": "ba025c37-3b33-461c-88a1-659a33f3cf47",
            "message": "The server is processing the request.",
            "upload_job": "https://localhost/api_v1/uploads/ba025c37-3b33-461c-88a1-659a33f3cf47/"
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :reqheader presqt-file-duplicate-action: Action to be taken if a duplicate file is found
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
    :statuscode 400: Project is not formatted correctly. Multiple directories exist at the top level
    :statuscode 400: Project is not formatted correctly. Files exist at the top level
    :statuscode 401: ``Token`` is invalid
    :statuscode 404: Invalid ``Target`` name

Upload To Existing Resource
+++++++++++++++++++++++++++

.. http:post::  /api_v1/targets/(str: target_name)/resources/(str: resource_id)/

    Upload a resource to an existing container. This endpoint begins the ``Upload``
    process. It returns a ``ticket_number`` which can be passed to the ``Upload Job`` endpoint to
    check in on the process.

    **Example request**:

    .. sourcecode:: http

        POST /api_v1/targets/OSF/resources/1234/ HTTP/1.1
        Host: localhost
        Accept: application/json

    **Example response**:

    ..  sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "ticket_number": "ba025c37-3b33-461c-88a1-659a33f3cf47",
            "message": "The server is processing the request.",
            "upload_job": "https://localhost/api_v1/uploads/ba025c37-3b33-461c-88a1-659a33f3cf47/"
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :reqheader presqt-file-duplicate-action: Action to be taken if a duplicate file is found
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
    :statuscode 401: ``Token`` is invalid
    :statuscode 403: User does not have access to this ``Resource``
    :statuscode 404: Invalid ``Target`` name
    :statuscode 410: ``Resource`` no longer available

Upload Job
++++++++++

.. http:get::  /api_v1/upload/(str: ticket_number)/

    Check on the ``Upload Process`` for the given ``ticket_number``.

    **Example request**:

    .. sourcecode:: http

        GET /api_v1/upload/ba025c37-3b33-461c-88a1-659a33f3cf47/ HTTP/1.1
        Host: localhost
        Accept: application/json

    **Example response if upload finished successfully**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/zip

        {
            "status_code": "200",
            "message": "Upload successful",
            "failed_fixity": ["/path/to/file/failed/fixity.jpg"],
            "resources_ignored": ["/path/to/file/ignored.jpg"],
            "resources_updated": ["/path/to/file/updated.jpg"]
        }

    **Example response if upload is in progress**:

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "status_code": null,
            "message": "Upload is being processed on the server"
        }

    **Example response if upload failed**:

    .. sourcecode:: http

        HTTP/1.1 500 Internal Server Error
        Content-Type: application/json

        {
            "status_code": "404",
            "message": "Resource with id 'bad_id' not found for this user."
        }

    :reqheader presqt-destination-token: User's ``Token`` for the destination target
    :statuscode 200: ``Upload`` has finished successfully
    :statuscode 202: ``Upload`` is being processed on the server
    :statuscode 400: ``presqt-destination-token`` missing in the request headers
    :statuscode 401: Header ``presqt-destination-token`` does not match the ``presqt-destination-token`` for this server process
    :statuscode 404: Invalid ``Ticket Number``
    :statuscode 500: Download failed on the server

Resource Transfer Endpoints
---------------------------

Transfer New Top Level Resource
+++++++++++++++++++++++++++++++

.. http:post::  /api_v1/targets/(str: target_name)/resources/

    Transfer a resource from a source target to a destination target. Make the resource a new
    top level resource, for instance a Project. This endpoint begins the ``Transfer``
    process. It returns a ``ticket_number`` which can be passed to the ``Transfer Job`` endpoint to
    check in on the process.

Transfer To Existing Resource
+++++++++++++++++++++++++++++

Transfer Job
++++++++++++