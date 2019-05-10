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
                    'kind': 'item',
                    'kind_name': 'file',
                    'id': file.id,
                    'container': container,
                    'title': file.name
                }
                resource_list.append(file_obj)
            elif kind == 'folder':
                folder = Folder(child, self.session)
                folder_obj = {
                    'kind': 'container',
                    'kind_name': 'folder',
                    'id': folder.id,
                    'container': container,
                    'title': folder.name
                }
                resource_list.append(folder_obj)

                folder_resource_objects = folder.get_resources_objects(folder.id)

                for folder in folder_resource_objects:
                   resource_list.append(folder)
        return resource_list


class Storage(OSFBase, ContainerMixin):
    """
    Class that represents a Storage provider in the OSF API.
    """

    def _populate_attributes(self, storage):
        """
        Add attributes to the class based on the JSON provided in the API call.

        Parameters
        ----------
        storage : dict
            Data dictionary returned from the json response to create the Storage class instance.
        """
        if not storage:
            return

        self.id = storage['id']

        self.path = storage['attributes']['path']
        self.name = storage['attributes']['name']
        self.node = storage['attributes']['node']
        self.provider = storage['attributes']['provider']
        self._files_url = storage['relationships']['files']['links']['related']['href']
        self._new_folder_url = storage['links']['new_folder']
        self._new_file_url = storage['links']['upload']

    def __str__(self):
        return '<Storage [{}]>'.format(self.id)


class Folder(OSFBase, ContainerMixin):
    """
    Class that represents a Folder in the OSF API
    """
    def _populate_attributes(self, folder):
        if not folder:
            return

        self.id = folder['id']
        self._endpoint = folder['links']['self']
        self._delete_url = folder['links']['delete']
        self._new_folder_url = folder['links']['new_folder']
        self._new_file_url = folder['links']['upload']
        self._move_url = folder['links']['move']
        self._files_url = folder['relationships']['files']['links']['related']['href']
        self.osf_path = folder['attributes']['path']
        self.path = folder['attributes']['materialized_path']
        self.name = folder['attributes']['name']
        self.date_created = folder['attributes']['date_created']
        self.date_modified = folder['attributes']['date_modified']

    def __str__(self):
        return '<Folder [{}, {}]>'.format(self.id, self.path)