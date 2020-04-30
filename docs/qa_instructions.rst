QA Testing Instructions
=======================

Getting Authorization Tokens From Partner Sites
-----------------------------------------------
An ``Authorization Token`` is a unique identifier for a user requesting access to a service.
`Click here <https://presqt.readthedocs.io/en/latest/authentication_authorization.html#taget-token-instructions>`_
for instructions on how to get authorization tokens for each target.

Resources
---------
We use the term ``resources`` for all content such as files, folders, projects, repos, items, etc.
It's a catch all term since different websites name their content differently.

Login To Targets From PresQT Demo UI
------------------------------------
1. Click on any Target icon under 'Available Connections' to pop open a login window.

.. figure:: images/qa/login/login_step_1.png
    :align: center

2. Copy your ``Authorization Token`` for the target and press ``Connect``

.. figure:: images/qa/login/login_step_2.png
    :align: center

3. Resources associated with this token will appear on the left side.
4. You can log out of the target and use a different token by pressing the button next to the resources header.

.. figure:: images/qa/login/login_step_3.png
    :align: center

5. To log into a different target simply repeat the process with a different target icon.
Once logged in you can switch between targets without having to provide your key.

Navigate and Searching The Resource Collection
----------------------------------------------
1. After logging in you can navigate through your ``Resource Collection`` by clicking on the folders and files on the left.
2. Clicking on a resource shows you the ``Resource Details`` on the right.

.. figure:: images/qa/resource_collection/resource_collection_step_1.png
    :align: center

3. Searching for public resources can be accomplished by selecting a search type and then pressing
the ``search icon``. Public resources will be shown in the ``Resource Collection``.
4. You can get back to your resources by pressing the ``refresh button``.

.. figure:: images/qa/resource_collection/resource_search_step_1.png
    :align: center
    :scale: 30%

Resource Details And Actions
----------------------------
1. Once you click on a resource you will get its details and buttons for each action available
for this resource. If the button is disabled then that action isn't available for that resource.

.. figure:: images/qa/resource_detail/resource_detail_step_1.png
    :align: center

Resource Download
-----------------
1. To download a resource, first select the resource in the ``resource collection`` and then click
the ``Download`` action button in the details section.

.. figure:: images/qa/resource_download/download_step_1.png
    :align: center

2. A modal will pop open providing you with transaction details. Click on the ``Download`` button
to start the download.

.. figure:: images/qa/resource_download/download_step_2.png
    :align: center

3. Once the download is complete, the modal will provide you with details about how the download
process went.

.. figure:: images/qa/resource_download/download_step_3.png
    :align: center

4. All downloads come in ``BagIt format``. After the download is complete, unzip the file,
and you will see BagIt specification files. The data you requested to downloaded will reside in
the ``data`` folder.

.. figure:: images/qa/resource_download/download_step_4.png
    :align: center
    :scale: 50%

Resource Upload
---------------

Upload As A New Project
+++++++++++++++++++++++
1. To upload to the target as a new project click the ``Create New Project`` button above the
``resource collection``.

.. figure:: images/qa/resource_upload/upload_new_step_1.png
    :align: center

2. A modal will pop open with an ``upload stepper``. First select the file you'd like to upload.
The file must be a zip file who's contents are in valid BagIt format.

.. figure:: images/qa/resource_upload/upload_new_step_2.png
    :align: center
    :scale: 30%

3. Next, the modal will display transaction details. Click ``Upload File`` to begin the upload process.

.. figure:: images/qa/resource_upload/upload_new_step_3.png
    :align: center
    :scale: 30%

4. Once the upload is completed, the modal will provide you with details about how the upload
process went.

.. figure:: images/qa/resource_upload/upload_new_step_4.png
    :align: center
    :scale: 30%

5. You should also see the new uploaded resources appear in the ``resource collection``.

Upload To An Existing Resource
++++++++++++++++++++++++++++++
1. To upload a resource, first select the resource in the ``resource collection`` and then click
the ``Upload`` action button in the details section.

.. figure:: images/qa/resource_upload/upload_existing_step_1.png
    :align: center

2. A modal will pop open with an ``upload stepper``. First select the file you'd like to upload.
The file must be a zip file who's contents are in valid BagIt format.

.. figure:: images/qa/resource_upload/upload_existing_step_2.png
    :align: center
    :scale: 30%

3. Select how you want PresQT to handle any duplicate files it finds existing in the resource already.
``Ignore`` will simply ignore the duplicate. ``Update`` will update the existing file with the new
uploaded file's contents if they differ.

.. figure:: images/qa/resource_upload/upload_existing_step_3.png
    :align: center
    :scale: 30%

4. Next, the modal will display transaction details. Click ``Upload File`` to begin the upload process.

.. figure:: images/qa/resource_upload/upload_existing_step_4.png
    :align: center
    :scale: 30%

5. Once the upload is completed, the modal will provide you with details about how the upload
process went.

.. figure:: images/qa/resource_upload/upload_existing_step_5.png
    :align: center
    :scale: 30%

6. You should also see the new uploaded resources appear in the ``resource collection``.

Resource Transfer
-----------------
1. To transfer a resource to another target, first select the resource in the ``resource collection``
and then click the ``Transfer`` button in the details section.

.. figure:: images/qa/resource_transfer/transfer_step_1.png
    :align: center

2. A modal will pop open with a ``transfer stepper``. First, select the target you want to ``transfer to`` and press the ``Next`` button.

.. figure:: images/qa/resource_transfer/transfer_step_2.png
    :align: center
    :scale: 30%

3. Input your token for the target you selected and press the ``Next`` button.

.. figure:: images/qa/resource_transfer/transfer_step_3.png
    :align: center
    :scale: 30%

4. Select the resource you want to transfer to. Don't select any resource if you want to create
a new project. Press ``Next`` once you have made your selection.

.. figure:: images/qa/resource_transfer/transfer_step_4.png
    :align: center
    :scale: 30%

5. Select how you want PresQT to handle any duplicate files it finds existing in the resource already.
``Ignore`` will simply ignore the duplicate. ``Update`` will update the existing file with the new
transferred file's contents if they differ. Press the ``Next`` button once you've made your selection.
If you are making a new project then just press ``Next``.

.. figure:: images/qa/resource_transfer/transfer_step_5.png
    :align: center
    :scale: 30%

6. Next, the modal will display transaction details. Click ``Transfer File`` to begin the transfer process.

.. figure:: images/qa/resource_transfer/transfer_step_6.png
    :align: center
    :scale: 30%

7. Once the transfer is completed, the modal will provide you with details about how the transfer
process went.

.. figure:: images/qa/resource_transfer/transfer_step_7.png
    :align: center
    :scale: 30%

8. You should also see the new transferred resources appear in the modal's ``resource collection`` on the right.


Services
--------

Send a Proposal to EaaSI
++++++++++++++++++++++++

TBD

