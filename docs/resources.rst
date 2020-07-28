Resources
=========
This page contains all relevant resources used during development

Links
-----
* |presqt_link|

.. |presqt_link| raw:: html

   <a href="https://presqt.crc.nd.edu/" target="_blank">PresQT Website</a>

* |osf_imp_link| 

.. |osf_imp_link| raw:: html

   <a href="https://osf.io/pn2ec/" target="_blank">OSF Implementation Effort</a>

* |github_code_link| 

.. |github_code_link| raw:: html

   <a href="https://github.com/ndlib/presqt" target="_blank">Github Code Repo</a>

* |dockerhub_link| 

.. |dockerhub_link| raw:: html

   <a href="https://hub.docker.com/r/presqt/presqt" target="_blank">Docker Hub Image</a>

* |video_link| 

.. |video_link| raw:: html

   <a href="https://drive.google.com/drive/folders/1FxFYatauUq5swIlPHwm4hAnlSBB41c7u?usp=sharing" target="_blank">Endpoint Videos</a>

* |eaasi_link| 

.. |eaasi_link| raw:: html

   <a href="https://www.softwarepreservationnetwork.org/eaasi/" target="_blank">EaaSI Website</a>

Example BagIts
--------------

BagIt Zip files
+++++++++++++++

Since the upload endpoint requires a BagIt file in zip format here are some pre-made zip files to test the upload endpoint.

:download:`#1 Valid BagIt For Top Level Container w/Folder <example_bagits/NewProjectWithFolderBagIt.zip>`

:download:`#2 Valid BagIt For Top Level Container w/File <example_bagits/NewProjectWithSingleFileBagIt.zip>`

:download:`#3 Valid BagIt For Existing Container w/Single File <example_bagits/SingleFileDuplicate.zip>`

:download:`#4 Valid BagIt For Existing Container w/Folders & Files <example_bagits/ExistingContainerBagIt.zip>`

:download:`#5 Invalid BagIt - Bad Manifest <example_bagits/BadBagItManifest.zip>`

:download:`#6 Invalid BagIt - Missing File <example_bagits/BadBagItMissingFile.zip>`

:download:`#7 Invalid BagIt - Unknown File <example_bagits/BadBagItUnknownfile.zip>`

Example Workflow
++++++++++++++++

The following are instructions on how the BagIt files above can be used to test the Upload endpoint:

1. Make a POST to ``https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/`` with BagIt #2 to see a new top level container created.
2. Get the id of the new container and make a POST to ``https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/{resource_id}/`` with BagIt #3 and with the 'presqt-file-duplicate-action' set to 'ignore' to see that the duplicate file is found and it's contents are different but the file is updated.
3. Make the same request as 2 but set the header 'presqt-file-duplicate-action' to 'update' to see the file updated.
4. With the same container id make a POST request to ``https://presqt-prod.crc.nd.edu/api_v1/targets/osf/resources/{resource_id}/`` with BagIt #4 to see new files and folders added to the top level container.
5. A POST request with BagIts 5-7 should return an error with nothing being uploaded.

.. toctree::
   :maxdepth: 3