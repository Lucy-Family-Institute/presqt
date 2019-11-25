Target Integration
==================
The goal of PresQT is to make it as simple as possible for a new target to integrate itself with the
PresQT services. Below are lists of code actions to take when integrating a target.

Target Endpoints
----------------
'Targets' are providers the PresQT API will connect to such as OSF, CurateND, HubZero, etc. Since
PresQT doesn't have a database, the Targets' information will be held in a JSON file located in
``/presqt/targets.json``.  You must add data to this file to integrate with PresQT.

Target Collection/Details
+++++++++++++++++++++++++

1. Add your target dictionary to the file ``presqt/targets.json``

    **Target JSON Details:**

        ============================ ===== ========================================================================
        name                         str   Name of the Target. This will be used as path parameters in the URL
        readable_name                str   Human readable name of the Target for the front end
        supported_actions            array Actions the target supports. Only make actions true when action is working
        resource_collection          bool  Get all resources for the user in this target
        resource_detail              bool  Get an individual resource's details
        resource_download            bool  Download a resource
        resource_upload              bool  Upload a resource
        resource_transfer_in         bool  Transfer a resource in to the target
        resource_transfer_out        bool  Transfer a resource out of the target
        supported_transfer_partners  dict  Targets this target can transfer in and out of
        transfer_in                  array Targets this target can accept transfers from
        transfer_out                 array Targets this target can transfer to
        supported_hash_algorithms    array The hash algorithms supported by the target
        infinite_depth               bool  Does the target support an infinite depth hierarchy?
        ============================ ===== ========================================================================

    **Target JSON Example:**

        .. code-block:: json

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
                    "transfer_in": ["github", "curate_nd"],
                    "transfer_out": ["github"]
                },
                "supported_hash_algorithms": ["sha256", "md5"],
                "infinite_depth": true
            }

    There is a management command that will validate ``targets.json`` that can be ran after you add your target.
    It can be run manually with:

        .. parsed-literal::
            $ python manage.py validate_target_json

    Otherwise the same management command is run when ``docker-compose up`` is ran.
    If the validation fails then it does not allow the docker containers to be spun up.

2. Add your target directory inside ``presqt/targets/``

    * Your target integration functionality will exist here.

Resource Endpoints
------------------

Resource Collection
+++++++++++++++++++
Targets that integrate with the Resources Collection API Endpoint must have a function that returns
a specifically structured dataset. This structure allows us to recreate the hierarchy of the file
structure on the front end.

1. Update your target in ``presqt/targets.json`` by setting
``supported_actions.resource_collection`` to ``true``.

2. Add a function to return the resource collection inside of your target directory.

    * If you would like to keep your file/function names consistent with what already exists
      add this function at ``presqt/targets/<target_name>/functions/fetch/<target_name>_fetch_resources()``

    * The function must have the following parameters **in this order**:

        ===== === ===========================
        token str User's token for the target
        ===== === ===========================

    * The function must return the following **in this order**:

        ========= ==== =============================================
        resources list list of Python dictionaries for each resource
        ========= ==== =============================================

            **Resource dictionary details:**

                ========= === =============================================================================================================
                kind      str Type of Resource

                              Options: [container, item]
                kind_name str Target specific name for that kind

                               For example OSF kind_names are: [node, folder, file]
                container str ID of the container for the resource.

                              For example if the resource is a file in a folder then the **container** value would be the ID of the folder

                              Can be None if the resource has no container
                id        str ID of the resource
                title     str Title of the resource
                ========= === =============================================================================================================

    **Example Resource Collection Function:**

        .. code-block:: python

            def <your_target_name>_fetch_resources(token):
                # Process to obtain resource collection goes here.
                # Variables below are defined here to show examples of structure.
                resources = [
                    {
                        'kind': 'container',
                        'kind_name': 'Project',
                        'id': '12345',
                        'container': None,
                        'title': 'New Project
                    },
                    {
                        'kind': 'item',
                        'kind_name': 'file',
                        'id': '34567,
                        'container': '12345',
                        'title': 'TheFile.jpg'
                    }
                ]
                return resources

3. Add the resource collection function to ``presqt/api_v1/utilities/utils/function_router.py``

    * Follow the naming conventions laid out in this class' docstring
    * This will make the function available in core PresQT code

Resource Detail
+++++++++++++++
Targets that integrate with the Resources Detail API Endpoint must have a function that returns
a specifically structured dataset that represents the resource.

1. Update your target in ``presqt/targets.json`` by setting
``supported_actions.resource_detail`` to ``true``.

2. Add a function to return the resource details inside of your target directory.

    * If you would like to keep your file/function names consistent with what already exists add this function at
      ``presqt/targets/<target_name>/functions/fetch/<target_name>_fetch_resource()``

    * The function must have the following parameters **in this order**:

        =========== === ====================================
        token       str User's token for the target
        resource_id str ID for the resource we want to fetch
        =========== === ====================================

    * The function must return the following **in this order**:

        ======== ====== =================================================
        resource object Python object representing the resource requested
        ======== ====== =================================================

        **Resource dictionary details:**

            ============= ==== ==================================================================
            kind          str  Type of Resource

                               Options: [container, item]
            kind_name     str  Target specific name for that kind

                               For example OSF kind_names are: [node, folder, file]
            id            str  ID of the resource
            title         str  Title of the resource
            date_created  str  Date the resource was created
            date_modified str  Date the resource was last modified
            hashes        dict Hashes of the resource in the target

                               Key must be the hash algorithm used value must be the hash itself

                               Can be an empty dict if no hashes exist
            extra         dict Any extra target specific data.

                               Can be an empty dict
            ============= ==== ==================================================================

        **Example Resource Collection Function:**

            .. code-block:: python

                def <your_target_name>_fetch_resource(token, resource_id):
                        # Process to obtain resource details goes here.
                        # Variables below are defined here to show examples of structure.

                    resource = {
                        "kind": "item",
                        "kind_name": "file",
                        "id": "12345",
                        "title": "o_o.jpg",
                        "date_created": "2019-05-13T14:54:17.129170Z",
                        "date_modified": "2019-05-13T14:54:17.129170Z",
                        "hashes": {
                            "md5": "abca7ef057dcab7cb8d79c36243823e4",
                            "sha256": "ea94ce55261720c56abb508c6dcd1fd481c30c09b7f2f5ab0b79e3199b7e2b55"
                        },
                        "extra": {
                            "category": "project",
                            "fork": false,
                            "current_user_is_contributor": true,
                            "preprint": false,
                            "current_user_permissions": [
                                "read",
                                "write",
                                "admin"
                            ],
                        }
                    }
                    return resource

3. Add the resource detail function to ``presqt/api_v1/utilities/utils/function_router.py``

    * Follow the naming conventions laid out in this class' docstring
    * This will make the function available in core PresQT code

Resource Download Endpoint
--------------------------
1. Update your target in ``presqt/targets.json`` by setting
``supported_actions.resource_download`` to ``true``.

2. Add a function to perform the resoucrce download inside of your target directory.

    * If you would like to keep your file/function names consistent with what already exists add this function at ``presqt/targets/<target_name>/functions/download/<target_name>_download_resource()``

    * The function must have the following parameters **in this order**:

        =========== === =======================================
        token       str User's token for the target
        resource_id str ID for the resource we want to download
        =========== === =======================================

    * The function must return a **dictionary** with the following keys:

        ================ ==== ==========================================================================================
        resources        list List of dictionaries containing resource data
        empty_containers list List of strings identifying empty container paths.

                              They need to be specified separately because they are written separate from the file data
        action_metadata  dict Dictionary containing FTS metadata about the action occurring
        ================ ==== ==========================================================================================

        **Resource Dictionary Details**

            ============== ===== ==================================================================
            file           bytes The file contents in byte format
            hashes         dict  Hashes of the resource in the target

                                 Key must be the hash algorithm used value must be the hash itself

                                 Can be an empty dict if no hashes exist
            title          str   Title of the file
            path           str   Path to save the file to at the destination

                                 Start the path with a ``/``
            source_path    str   Full path of the file at the source

                                 Start the path with a ``/``

            extra_metadata dict  Dictionary containing any extra data to save to FTS metadata
            ============== ===== ==================================================================

        **Action Metadata Dictionary Details**

            ============== === ============================================================
            sourceUsername str Username of the user making the request at the source target
            ============== === ============================================================

    **Example Resource Download Function:**

        .. code-block:: python

            def <your_target_name>_download_resource(token, resource_id):
                # Process to download resource goes here.
                # Variables below are defined here to show examples of structure.
                resources = [
                    {
                        'file': binary_file_contents,
                        'hashes': {'md5': '1ab2c3d4e5f6g', 'sha256': 'fh3383h83fh'},
                        'title': 'file.jpg',
                        'path': '/path/to/file.jpg',
                        'source_path': 'project_name/path/to/file.jpg',
                        'extra_metadata': {
                            'dateSubmitted': '2019-10-22Z',
                            'creator': 'Justin Branco',
                        }
                    },
                    {
                        'file': binary_file_contents,
                        'hashes': {'md5': 'zadf23fg3', 'sha256': '9382hash383h'},
                        'title': 'funnysong.mp3',
                        'path': '/path/to/file/funnysong.mp3'
                        'source_path': 'project_name/path/to/file/funnysong.mp3',
                        'extra_metadata': {
                            'dateSubmitted': '2019-10-22Z',
                            'creator': 'Justin Branco',
                        }
                    }
                ]
                empty_containers = ['path/to/empty/container/', 'another/empty/']
                action_metadata = {"sourceUsername": contributor_name}
                return resources, empty_containers

3. Add the resource download function to ``presqt/api_v1/utilities/utils/function_router.py``

    * Follow the naming conventions laid out in this class' docstring
    * This will make the function available in core PresQT code

Resource Upload Endpoint
------------------------
1. Update your target in ``presqt/targets.json`` by setting
``supported_actions.resource_upload`` to ``true``.

2. Add a function to perform the resource upload inside of your target directory.

    * If you would like to keep your file/function names consistent with what already exists add this function at ``presqt/targets/<target_name>/functions/upload/<target_name>_upload_resource()``

    * The function must have the following parameters **in this order**:

        ===================== === ==========================================================================
        token                 str User's token for the target
        resource_id           str ID of the resource requested
        resource_main_dir     str Path to the main directory on the server for the resources to be uploaded
        hash_algorithm        str Hash algorithm we are using to check for fixity
        file_duplicate_action str The action to take when a duplicate file is found

                                  Options: [ignore, update]
        ===================== === ==========================================================================

    * The function must return a **dictionary** with the following keys:

        ================== ===== =================================================================================
        resources_ignored  array Array of string paths of files that were ignored when uploading the resource

                                 Path should have the same base as resource_main_dir
        resources_updated  array Array of string paths of files that were updated when uploading the resource

                                 Path should have the same base as resource_main_dir
        file_metadata_list list  List of dictionaries that contains FTS metadata and hash info for each file
        action_metadata    dict  Dictionary containing FTS metadata about the action occurring
        project_id         str   ID of the parent project for this upload. Needed for metadata upload
        ================== ===== =================================================================================

        **Metadata Dictionary Details**

            =============== ==== =============================================================================================================
            actionRootPath  str  Original path of the file on the server before upload.

                                 This is used to connect this metadata with download metadata if the action is a transfer.
            destinationHash dict Hash of the resource in the target that was calculated using the hash_algorithm given as a function parameter

                                 Key must be the hash algorithm used value must be the hash itself

                                 Can be an empty dict if no hashes exist
            destinationPath str  Full path of the file at the destination

                                 Start the path with a ``/``
            title           str  Title of the file
            =============== ==== =============================================================================================================

        **Action Metadata Dictionary Details**

            =================== === =================================================================
            destinationUsername str Username of the user making the request at the destination target
            =================== === =================================================================

    **Example Resource Upload Function:**

        .. code-block:: python

            def <your_target_name>_upload_resource(token, resource_id, resource_main_dir,
                                    hash_algorithm, file_duplicate_action):
                # Process to upload resource goes here.
                # Variables below are defined here to show examples of structure.
                file_metadata_list = [
                    {
                        "actionRootPath": 'resource_main_dir/path/to/updated/file.jpg',
                        "destinationPath": '/path/to/updated/file.jpg',
                        "title": 'file.jpg,
                        "destinationHash": {'md5': '123456'} # hash_algorithm = 'md5'
                    }
                ]
                resources_ignored = ['path/to/ignored/file.png', 'another/ignored/file.jpg']
                resources_updated = ['path/to/updated/file.jpg']
                action_metadata = {"destinationUsername": 'destination_username'}

                return {
                    'resources_ignored': resources_ignored,
                    'resources_updated': resources_updated,
                    'action_metadata': action_metadata,
                    'file_metadata_list': file_metadata_list,
                    'project_id': '1234'
                }

3. Add a function to upload FTS metadata to the correct location within the resource's parent project.

    * If you would like to keep your file/function names consistent with what already exists add this function at ``presqt/targets/<target_name>/functions/upload_metadata/<target_name>_upload_metadata()``

    * The function must have the following parameters **in this order**:

        ============= ==== ======================================================
        token         str  User's token for the target
        metadata_dict dict The FTS metadata dictionary to upload

                           At this point it will be a Python dict
        project_id    str  The id of the parent project for the resource uploaded
        ============= ==== ======================================================

    * The function doesn't return anything

    **Example Resource Upload Function:**

        .. code-block:: python

            def <your_target_name>_upload_metadata(token, metadata_dict, project_id):
                # Process to upload metadata goes here.

3. Add the resource upload and upload metadata functions to  ``presqt/api_v1/utilities/utils/function_router.py``

    * Follow the naming conventions laid out in this class' docstring
    * This will make the function available in core PresQT code

Resource Transfer Endpoint
--------------------------
1. Update your target in ``presqt/targets.json`` by setting
``supported_actions.resource_transfer_in``, ``supported_actions.resource_transfer_out``,
``supported_actions.supported_transfer_partners.transfer_in``, and
``supported_actions.supported_transfer_partners.transfer_out`` appropriately.

The resource transfer endpoint utilizes the Download and Upload functions. If these two functions
are in place then transfer is available.

Error Handling
--------------
When any of these target functions are called within PresQT core code they are wrapped inside of a
``Try-Except`` clause which looks for the exception ``PresQTResponseException``. The definition of this
exception can be found at ``presqt.utilities.exceptions.exceptions.PresQTResponseException``.

