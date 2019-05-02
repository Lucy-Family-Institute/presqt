from presqt.osf.osf_classes.osf_core import OSFCore
from presqt.osf.osf_classes.osf_file import File

class ContainerMixin:
    def _iter_children(self, url, kind, klass, recurse=None):
        """
        Iterate over all children of `kind`.
        Yield an instance of `klass` when a child is of type `kind`.
        Uses `recurse` as the path of attributes in the JSON returned from `url` to find
        more children.
        """
        children = self._follow_next(url)

        while children:
            child = children.pop()
            kind_ = child['attributes']['kind']
            if kind_ == kind:
                yield klass(child, self.session)
            elif recurse is not None:
                # recurse into a child and add entries to `children`
                value = child
                for key in recurse:
                    value = value[key]
                children.extend(self._follow_next(value))

    @property
    def top_level_files(self):
        """
        Iterate over all files in this container.
        It does not recursively find all files.
        Only lists files in this container.
        """
        return self._iter_children(self._files_url, 'file', File)

    @property
    def folders(self):
        """
        Iterate over top-level folders in this container.
        """
        return self._iter_children(self._files_url, 'folder', Folder)

    def get_assets_objects(self, container):
        """
        Get all assets for this container including the original container.
        This exists so we can get all assets in the structure we want for our API payloads.
        """
        asset_list = []
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
                asset_list.append(file_obj)
            elif kind == 'folder':
                folder = Folder(child, self.session)
                folder_obj = {
                    'kind': 'container',
                    'kind_name': 'folder',
                    'id': folder.id,
                    'container': container,
                    'title': folder.name
                }
                asset_list.append(folder_obj)

                folder_asset_objects = folder.get_assets_objects(folder.id)

                for folder in folder_asset_objects:
                    asset_list.append(folder)
        return asset_list

class Storage(OSFCore, ContainerMixin):
    """
    Class that represents a Storage provider in the OSF API.
    """

    def _update_attributes(self, storage):
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

    @property
    def files(self):
        """
        Iterate over all files in this storage. Recursively lists all files in all subfolders.
        """
        return self._iter_children(self._files_url, 'file', File,
                                   ('relationships', 'files', 'links', 'related', 'href'))


class Folder(OSFCore, ContainerMixin):
    """
    Class that represents a Folder in the OSF API
    """
    def _update_attributes(self, folder):
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