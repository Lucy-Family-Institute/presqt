from presqt.osf.osf_classes.osf_core import OSFCore
from presqt.osf.osf_classes.osf_project import Project


class OSF(OSFCore):
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

        Parameters
        ----------
        project_id : str
            id of the Project we want to fetch.

        Returns
        -------
        Instance of the desired Project.
        """
        type_ = self.guid(project_id)
        url = self._build_url(type_, project_id)
        if type_ in Project._types:
            return Project(self._json(self._get(url)), self.session)
        raise RuntimeError('{} is unrecognized type {}. '
                           'Supports projects and registrations'.format(project_id, type_))

    def guid(self, guid):
        """
        Determines JSONAPI type for provided GUID
        """
        return self._json(self._get(self._build_url('guids', guid)))['data']['type']

    def projects(self):
        """
        Fetch all projects for this user.
        """
        url = self._build_url('users', 'me', 'nodes')
        response_json = self._json(self._get(url))
        node_urls = [self._build_url('nodes', node['id']) for node in response_json['data']]
        projects = [Project(self._json(self._get(node)), self.session) for node in node_urls]
        return projects

    def get_user_assets(self, assets):
        """
        Get all of the user's assets. Return in the structure expected for the PresQT API.

        Parameters
        ----------
        assets : list
            Reference to the list of assets we want to add to.

        Returns
        -------
        List of all assets.
        """
        for project in self.projects():
            project.get_assets(assets)
        return assets