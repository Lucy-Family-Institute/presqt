from presqt.osf.classes.base import OSFBase
from presqt.osf.classes.file import File
from presqt.osf.classes.project import Project
from presqt.osf.classes.storage_folder import Folder, Storage


class OSF(OSFBase):
    """
    Interact with the Open Science Framework.
    This is the main point of contact for interactions with the OSF.
    Use the methods of this class to find projects, login to the OSF, etc.
    """
    def __init__(self, token):
        super(OSF, self).__init__({})
        self.login(token)

    def login(self, token):
        """
        Login user for API calls.
        """
        self.session.token_auth(token)

    def project(self, project_id):
        """
        Get a project with the given project_id.

        Parameters
        ----------
        project_id : str
            id of the Project we want to fetch.

        Returns
        -------
        Instance of the desired Project.
        """
        url = self.session.build_url('nodes', project_id)
        return Project(self._json(self.session.get(url)), self.session)

    def resource(self, resource_id):
        """
        Gets a file or folder with the given id.

        Parameters
        ----------
        resource_id : str
            id of the resource we want to fetch.

        Returns
        -------
        Instance of the desired resource (either Folder or File).
        """
        url = self.session.build_url('files', resource_id)
        response_json = self._json(self.session.get(url))['data']

        if response_json['attributes']['kind'] == 'file':
            return File(response_json, self.session)
        else:
            return Folder(response_json, self.session)

    # def storage(self, resource_id):
    #     """
    #     Get a storage folder with the given id.
    #
    #     Parameters
    #     ----------
    #     resource_id : str
    #         id of the resource we want to fetch.
    #
    #     Returns
    #     -------
    #     Instance of the desired storage folder.
    #     """
    #     resource_split = resource_id.split(':')
    #     url = self.session.build_url('nodes', resource_split[0])
    #     response_json = self._json(self.session.get(url))
    #     project = Project(response_json, self.session)
    #     return project.storage(resource_split[1])

    def projects(self):
        """
        Fetch all projects for this user.
        """
        url = self.session.build_url('users', 'me', 'nodes')
        response_json = self._json(self.session.get(url))
        node_urls = [self.session.build_url('nodes', node['id']) for node in response_json['data']]

        projects = [Project(self._json(self.session.get(node_url)), self.session) for node_url in node_urls]
        return projects

    def get_user_resources(self):
        """
        Get all of the user's resources. Return in the structure expected for the PresQT API.

        Returns
        -------
        List of all resources.
        """
        resources = []
        for project in self.projects():
            project.get_resources(resources)
        return resources