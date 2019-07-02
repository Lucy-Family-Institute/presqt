import os

from requests.exceptions import ConnectionError
from rest_framework import status

from presqt.api_v1.utilities import read_file
from presqt.exceptions import PresQTResponseException
from presqt.osf.classes.base import OSFBase
from presqt.osf.classes.file import File

class ContainerMixin:
    def get_resources_objects(self, container):
        """
        Get all resources for this container including the original container.
        This exists so we can get all resources in the structure we want for our API payloads.
        """
        resource_list = []
        children = self._follow_next(self._files_url)

        while children:
            child = children.pop()
            kind = child['attributes']['kind']
            if kind == 'file':
                file = File(child, self.session)
                file_obj = {
                    'kind': file.kind,
                    'kind_name': file.kind_name,
                    'id': file.id,
                    'container': container,
                    'title': file.title
                }
                resource_list.append(file_obj)
            elif kind == 'folder':
                folder = Folder(child, self.session)
                folder_obj = {
                    'kind': folder.kind,
                    'kind_name': folder.kind_name,
                    'id': folder.id,
                    'container': container,
                    'title': folder.title
                }
                resource_list.append(folder_obj)

                for resource in folder.get_resources_objects(folder.id):
                   resource_list.append(resource)

        return resource_list

    def get_all_files(self):
        """
        Recursively gets all files for a given container.
        """
        file_list = []
        children = self._follow_next(self._files_url)
        while children:
            child = children.pop()
            kind = child['attributes']['kind']

            if kind == 'file':
                file_list.append(File(child, self.session))
            elif kind == 'folder':
                folder = Folder(child, self.session)

                for file in folder.get_all_files():
                    file_list.append(file)

        return file_list

    def iter_children(self, url, kind, klass, recurse=None):
        """
        Iterate over all children of `kind`.
        """
        children = self._follow_next(url)

        while children:
            child = children.pop()
            kind_ = child['attributes']['kind']
            if kind_ == kind:
                yield klass(child, self.session)
            elif recurse is not None:
                # recurse into a child and add entries to `children`
                url = self._get_attribute(child, *recurse)
                children.extend(self._follow_next(url))

    def get_folder_by_name(self, folder_name):
        """
        Gets a folder object based on the name. Only looks for top level folders.
        """
        for folder in self.iter_children(self._files_url, 'folder', Folder):
            if folder.title == folder_name:
                return folder
        else:
            return None

    def get_file_by_name(self, file_name):
        """
        Gets a file object based on the name. Only looks for top level files.
        """
        for file in self.iter_children(self._files_url, 'file', File):
            if file.title == file_name:
                return file
            else:
                return None

    def create_folder(self, folder_name):
        """
        Create a new sub-folder for this container
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

    def create_file(self, file_name, file_to_write):
        """
        Upload a file to a container.
        """

        # When uploading a large file (>a few MB) that already exists
        # we sometimes get a ConnectionError instead of a status == 409.
        connection_error = False
        try:
            response = self.put(self._new_file_url, params={'name': file_name}, data=file_to_write)
        except ConnectionError:
            connection_error = True

        if connection_error or response.status_code == 409:
            return self.get_file_by_name(file_name)

        elif response.status_code == 201:
            return self.get_file_by_name(file_name)

        else:
            raise PresQTResponseException(
                "Response has status code {} while creating folder {}".format(response.status_code,
                                                                              file_name),
                status.HTTP_400_BAD_REQUEST)


    def create_directory(self, directory_path):
        """
        Create a directory of folders and files found in the given directory_path.
        """
        directory, folders, files = next(os.walk(directory_path))

        for file in files:
            file_to_write = read_file('{}/{}'.format(directory, file))
            self.create_file(file, file_to_write)

        for folder in folders:
            created_folder = self.create_folder(folder)
            created_folder.create_directory('{}/{}'.format(directory, folder))


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
