from rest_framework import status

from presqt.targets.osf.classes.base import OSFBase
from presqt.targets.osf.classes.storage_folder import Storage
from presqt.targets.osf.exceptions import OSFNotFoundError


class Project(OSFBase):
    """
    Class that represents a project in the OSF API.
    """
    def __init__(self, project, session):
        super(Project, self).__init__(project, session)

        # Add attributes to the class based on the JSON provided in the API call
        project = project['data']
        self.id = project['id']
        # Links
        self._endpoint = project['links']['self']
        self._storages_url = project['relationships']['files']['links']['related']['href']
        # Attributes
        attrs = project['attributes']
        self.kind = 'container'
        self.kind_name = 'project'
        self.category = attrs['category']
        self.fork = attrs['fork']
        self.current_user_is_contributor = attrs['current_user_is_contributor']
        self.preprint = attrs['preprint']
        self.description = attrs['description']
        self.current_user_permissions = attrs['current_user_permissions']
        self.title = attrs['title']
        self.custom_citation = attrs['custom_citation']
        self.date_modified = attrs['date_modified']
        self.collection = attrs['collection']
        self.public = attrs['public']
        self.subjects = attrs['subjects']
        self.registration = attrs['registration']
        self.date_created = attrs['date_created']
        self.current_user_can_comment = attrs['current_user_can_comment']
        self.node_license = attrs['node_license']
        self.wiki_enabled = attrs['wiki_enabled']
        self.tags = attrs['tags']
        self.size = None
        self.sha256 = None
        self.md5 = None

    def storages(self):
        """
        Iterate over all storages for this project.
        """
        stores_json = self._json(self.get(self._storages_url))
        for store in stores_json['data']:
            yield Storage(store, self.session)

    def storage(self, storage):
        """
        Get a storage attached to the project.

        Parameters
        ----------
        storage : str
            Storage name

        Returns
        -------
        Project object.
        """
        for store in self.storages():
            if store.provider == storage:
                return store
        else:
            raise OSFNotFoundError("Project has no storage provider '{}'".format(storage),
                                    status.HTTP_404_NOT_FOUND)

    def get_resources(self, resources):
        """
        Get all project resources. Return in the structure expected for the PresQT API.

        Parameters
        ----------
        resources : list
            Reference to the list of resources we want to add to.

        Returns
        -------
        List of project resources.
        """
        node_obj = {
            'kind': 'container',
            'kind_name': 'project',
            'id': self.id,
            'container': None,
            'title': self.title
        }
        resources.append(node_obj)

        for storage in self.storages():
            storage_obj = {
                'kind': 'container',
                'kind_name': 'storage',
                'id': storage.id,
                'container': self.id,
                'title': storage.title
            }
            resources.append(storage_obj)

            for resource in storage.get_resources_objects(storage.id):
                resources.append(resource)

        return resources

    def get_all_files(self):
        files = []
        for storage in self.storages():
            [files.append(file) for file in storage.get_all_files()]
        return files