Developer Documentation
=======================
Low level documentation such as development environment setup, API endpoints, code documentation.


Resource Collection
-------------------

Resource Detail
---------------
    * **Function returns:**
        * *resource object: python dictionary*
            * See Resource Endpoint docs for details/example. 
* Add the resource collection function to ``presqt/api_v1/utilities/utils/function_router.py``
    * Follow the naming conventions laid out in this class' docstring

Resource Download
-----------------
* Add functionality to return a list of downloaded files inside of your target directory.
    * **Function parameters in order:**
        * *token: str*
            * User's token for the target
        * *resource_id: str*
            * ID for the resource we want to fetch
    * **Function returns:**
        * *list of downloads: list of python dictionaries*
            * Each dictionary will contain details for each file that we can use to build a BagIt 
              zip file to return. See the example below for more details.
        * *list of empty containers: list of strings*
            * This list will contain container paths that don't have files. This will allow us to 
              write any empty directories to the BagIt zip file.

   .. code-block:: python

        def <your_target_name>_download_resource(token, resource_id):
            """
            Parameters
            ----------
            token : str
                User's token

            resource_id : str
                ID of the resource requested

            Returns
            -------
            - List of dictionary objects that each hold a file and its information.
                Dictionary must be in the following format:
                {
                    'file': binary_file, # File contents in binary format
                    'hashes': {'md5': 'the_hash}, # Dictionary of file hashes in target
                    'title': 'file.jpg', # Title of the file
                    'path': '/path/to/file # path of the file relative to starting container
                }
            - List of string paths representing empty containers that must be written.
                Example: ['empty/folder/to/write/', 'another/empty/folder/]
            """
            
            # Download process goes here. Variables below are calculated during the upload process
            # But are defined here to show examples of structure 
            
            files = [
                {
                    'file': binary_file_contents,
                    'hashes': {'md5': '1ab2c3d4e5f6g', 'sha256': 'fh3383h83fh'},
                    'title': 'file.jpg',
                    'path': '/path/to/file.jpg'
                },
                {
                    'file': binary_file_contents,
                    'hashes': {'md5': 'zadf23fg3', 'sha256': '9382hash383h'},
                    'title': 'funnysong.mp3',
                    'path': '/path/to/file/funnysong.mp3'
                }
            ]
            empty_containers = ['path/to/empty/container/', 'another/empty/']
            return files, empty_containers


Resource Upload
---------------
* Add functionality to upload files to the target destination.
    * **Function parameters in order:**
        * *token: str*
            * User's token for the target
        * *resource_id: str*
            * ID for the resource we want to fetch
            * This can be 'None'
        * *resource_main_dir: str*
            * Path of the main directory where the resources are located on the server
        * *hash_algorithm: str*
            * Hash algorithm we want to get from the Target after it the resources are uploaded
        * *file_duplicate_action: str*
            * The action to take when a duplicate file is found
            * Options are 'ignore' or 'update'
    * **Function returns:**
        * *dictionary of hashes: python dictionaries*
            * Dictionary of files hashes calculated using the hash algorithm provided obtained from 
              the target after upload.
        * *list of files ignored: list of strings*
            * List of duplicate files ignored during the upload process
            * File path must include full path starting with the resource_main_dir provided
        * *list of files_updated: list of strings*
            * List of duplicate files updated during the upload process
            * File path must include full path starting with the resource_main_dir provided

   .. code-block:: python

        def <your_target_name>_upload_resource(token, resource_id, resource_main_dir,
                                hash_algorithm, file_duplicate_action):
            """
            Parameters
            ----------
            token : str
                User's token.
            resource_id : str
                ID of the resource requested.
            resource_main_dir : str
                Path to the main directory for the resources to be uploaded.
            hash_algorithm : str
                Hash algorithm we are using to check for fixity.
            file_duplicate_action : str
                The action to take when a duplicate file is found

            Returns
            -------
            final_file_hashes : dict
                Dictionary of file hashes obtained from the target
                Example:
                {
                    'mediafiles/uploads/25/BagItToUpload/data/NewProj/funnyimages/Screen.png':
                    '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141ea',
                    'mediafiles/uploads/25/BagItToUpload/data/NewProj/funnyimages/Screen2.png':
                    '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141eb',
                }
            files_ignored : array
                Array of string file paths of files that were ignored when uploading the resource
                ['path/to/ignored/file.pg', 'another/ignored/file.jpg']

            files_updated : array
                Array of string file paths of files that were updated when uploading the resource
                ['path/to/updated/file.jpg']
            """
            
            # Upload process goes here. Variables below are calculated during the upload process
            # But are defined here to show examples of structure 
            
            final_file_hashes = {
                'mediafiles/uploads/25/BagItToUpload/data/NewProj/funnyimages/Screen.png':
                '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141ea',
                'mediafiles/uploads/25/BagItToUpload/data/NewProj/funnyimages/Screen2.png':
                '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141eb',
            }
            files_ignored = ['path/to/ignored/file.pg', 'another/ignored/file.jpg']
            files_updated = ['path/to/updated/file.jpg']
            
            return final_file_hashes, files_ignored, files_updated

Resource Transfer
-----------------
The resource Transfer endpoint actually utilizes the Download and Upload functions so no further 
functionality is required.

.. toctree::
   :maxdepth: 3