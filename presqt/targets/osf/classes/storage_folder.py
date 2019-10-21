import os

from requests.exceptions import ConnectionError
from rest_framework import status

from presqt.api_v1.utilities import hash_generator
from presqt.utilities import read_file
from presqt.utilities import PresQTResponseException
from presqt.targets.osf.classes.base import OSFBase
from presqt.targets.osf.classes.file import File
from presqt.targets.osf.utilities import osf_download_metadata


class ContainerMixin:
    def get_all_files(self, initial_path, files, empty_containers):
        """
        Recursively gets all files for a given container.
        """
        children = self._get_all_paginated_data(self._files_url)

        # If this is an empty container then we need to update the empty_containers list
        if not children:
            if self.kind_name == 'folder':
                path = '{}/{}/'.format(initial_path, self.title)
            else:
                path = '{}/'.format(initial_path)
            empty_containers.append(path)

        while children:
            child = children.pop()
            kind = child['attributes']['kind']

            if kind == 'file':
                file = File(child, self.session)
                file_metadata = osf_download_metadata(file)
                files.append({
                    'file': file,
                    'hashes': file.hashes,
                    'title': file.title,
                    'path': '{}{}'.format(initial_path, file.materialized_path),
                    'metadata': file_metadata
                })
            elif kind == 'folder':
                folder = Folder(child, self.session)

                folder.get_all_files(initial_path, files, empty_containers)

    def iter_children(self, url, kind, klass):
        """
        Iterate over all children of `kind`.

        Parameters
        ----------
        url : str
            URL to get the current children data points.
        kind : str
            The kind of resource we are attempting to get.
        klass :str
            The resource's kind associated class
        """
        children = self._get_all_paginated_data(url)

        while children:
            child = children.pop()
            kind_ = child['attributes']['kind']
            if kind_ == kind:
                yield klass(child, self.session)

    def get_folder_by_name(self, folder_name):
        """
        Gets a folder object based on the name. Only looks for top level folders.

        Parameters
        ----------
        folder_name : str
            Name of the folder we want to find within the container.

        Returns
        -------
        Returns an instance of the requested Folder class.
        """
        for folder in self.iter_children(self._files_url, 'folder', Folder):
            if folder.title == folder_name:
                return folder

    def get_file_by_name(self, file_name):
        """
        Gets a file object based on the name. Only looks for top level files.

        Parameters
        ----------
        file_name : str
            Name of the file we want to find within the container.

        Returns
        -------
        Returns an instance of the requested File class.
        """
        for file in self.iter_children(self._files_url, 'file', File):
            if file.title == file_name:
                return file

    def create_folder(self, folder_name):
        """
        Create a new sub-folder for this container.

        Parameters
        ----------
        folder_name : str
            Name of the folder to create.

        Returns
        -------
        Class instance of the created folder.
        """
        response = self.put(self._new_folder_url, params={'name': folder_name})
        if response.status_code == 409:
            return self.get_folder_by_name(folder_name)

        elif response.status_code == 201:
            return self.get_folder_by_name(folder_name)

        else:
            raise PresQTResponseException(
                "Response has status code {} while creating folder {}".format(response.status_code,
                                                                              folder_name),
                status.HTTP_400_BAD_REQUEST)

    def create_file(self, file_name, file_to_write, file_duplicate_action):
        """
        Upload a file to a container.

        Parameters
        ----------
        file_name : str
            Name of the file to create.
        file_to_write : bytes
            File to create.
        file_duplicate_action : str
            Flag for how to handle the case of the file already existing.

        Returns
        -------
        Class instance of the created file.
        """
        # When uploading a large file (>a few MB) that already exists
        # we sometimes get a ConnectionError instead of a status == 409.
        connection_error = False
        try:
            response = self.put(self._new_file_url, params={'name': file_name}, data=file_to_write)
        except ConnectionError:
            connection_error = True

        # If the file is a duplicate then either ignore or update it
        if connection_error or response.status_code == 409:
            original_file = self.get_file_by_name(file_name)

            if file_duplicate_action == 'ignore':
                return 'ignored', original_file

            elif file_duplicate_action == 'update':
                # Only attempt to update the file if the new file is different than the original
                if hash_generator(file_to_write, 'md5') != original_file.hashes['md5']:
                    response = self.get_file_by_name(file_name).update(file_to_write)

                    if response.status_code == 200:
                        return 'updated', self.get_file_by_name(file_name)
                    else:
                        raise PresQTResponseException(
                            "Response has status code {} while updating file {}".format(
                                response.status_code, file_name), status.HTTP_400_BAD_REQUEST)
                else:
                    return 'ignored', original_file

        # File uploaded successfully
        elif response.status_code == 201:
            return 'created', self.get_file_by_name(file_name)

        else:
            raise PresQTResponseException(
                "Response has status code {} while creating file {}".format(response.status_code,
                                                                            file_name),
                status.HTTP_400_BAD_REQUEST)

    def create_directory(self, directory_path, file_duplicate_action, file_hashes,
                         resources_ignored, resources_updated, file_metadata_list):
        """
        Create a directory of folders and files found in the given directory_path.

        Parameters
        ----------
        directory_path : str
            Directory to find the resources to create.
        file_duplicate_action : str
            Flag for how to handle the case of the file already existing.
        file_hashes : dict
            Dictionary of uploaded file hashes.
        resources_ignored : list
            List of duplicate resources ignored.
        resources_updated : list
            List of duplicate resources updated.

        Returns
        -------
        Returns same file_hashes, resources ignored, resources updated parameters.
        """
        directory, folders, files = next(os.walk(directory_path))

        for filename in files:
            file_path = '{}/{}'.format(directory, filename)
            file_to_write = read_file(file_path)

            action, file = self.create_file(filename, file_to_write, file_duplicate_action)

            file_metadata_list.append({
                "actionRootPath": file_path,
                "destinationPath": '{}{}'.format(file.provider, file.materialized_path),
                "title": file.title,
                "destinationHash": file.hashes})

            file_hashes[file_path] = file.hashes
            if action == 'ignored':
                resources_ignored.append(file_path)
            elif action == 'updated':
                resources_updated.append(file_path)

        for folder in folders:
            created_folder = self.create_folder(folder)
            created_folder.create_directory('{}/{}'.format(directory, folder),
                                            file_duplicate_action, file_hashes,
                                            resources_ignored, resources_updated, file_metadata_list)




class Storage(OSFBase, ContainerMixin):
    """
    Class that represents a Storage provider in the OSF API.
    """

    def __init__(self, storage, session):
        super(Storage, self).__init__(storage, session)

        # Add attributes to the class based on the JSON provided in the API call
        self.id = storage['id']
        # Links
        self._files_url = storage['relationships']['files']['links']['related']['href']
        self._new_folder_url = storage['links']['new_folder']
        self._new_file_url = storage['links']['upload']
        # Attributes
        attrs = storage['attributes']
        self.node = attrs['node']
        self.path = attrs['path']
        self.kind = 'container'
        self.kind_name = 'storage'
        self.title = attrs['name']
        self.provider = attrs['provider']
        self.size = None
        self.date_created = None
        self.date_modified = None
        self.sha256 = None
        self.md5 = None


class Folder(OSFBase, ContainerMixin):
    """
    Class that represents a Folder in the OSF API
    """

    def __init__(self, folder, session):
        super(Folder, self).__init__(folder, session)

        # Add attributes to the class based on the JSON provided in the API call
        self.id = folder['id']
        related = folder['relationships']['target']['links']['related']
        if related['meta']['type'] == 'node':
            self.parent_project_id = related['href'][-6:-1]
        # Links
        self._endpoint = folder['links']['self']
        self._delete_url = folder['links']['delete']
        self._new_folder_url = folder['links']['new_folder']
        self._new_file_url = folder['links']['upload']
        self._move_url = folder['links']['move']
        self._files_url = folder['relationships']['files']['links']['related']['href']
        # Attributes
        attrs = folder['attributes']
        self.kind = 'container'
        self.kind_name = 'folder'
        self.title = attrs['name']
        self.last_touched = attrs['last_touched']
        self.materialized_path = attrs['materialized_path']
        self.date_modified = attrs['date_modified']
        self.current_version = attrs['current_version']
        self.date_created = attrs['date_created']
        self.provider = attrs['provider']
        self.path = attrs['path']
        self.current_user_can_comment = attrs['current_user_can_comment']
        self.guid = attrs['guid']
        self.checkout = attrs['checkout']
        self.tags = attrs['tags']
        self.size = attrs['size']
        # Extra
        self.sha256 = None
        self.md5 = None
