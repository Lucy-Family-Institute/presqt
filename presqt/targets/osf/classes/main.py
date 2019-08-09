import json

import requests
from rest_framework import status

from presqt.utilities import PresQTResponseException, PresQTInvalidTokenError
from presqt.targets.osf.classes.base import OSFBase
from presqt.targets.osf.classes.file import File
from presqt.targets.osf.classes.project import Project
from presqt.targets.osf.classes.storage_folder import Folder


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

        Parameters
        ----------
        token : str
            Token of the user performing the request.

        """
        self.session.token_auth(token)
        # Verify that the token provided is a valid one.
        response = requests.get('https://api.osf.io/v2/users/me/',
                                headers={'Authorization': 'Bearer {}'.format(token)})
        if response.status_code == 401:
            raise PresQTInvalidTokenError("Token is invalid. Response returned a 401 status code.")

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
        return Project(self._json(self.get(url)), self.session)

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
        response_json = self._json(self.get(url))['data']

        if response_json['attributes']['kind'] == 'file':
            return File(response_json, self.session)
        else:
            return Folder(response_json, self.session)

    def projects(self):
        """
        Fetch all projects for this user.
        """
        url = self.session.build_url('users', 'me', 'nodes')
        response_data = self._follow_next(url)
        node_urls = [self.session.build_url('nodes', node['id']) for node in response_data]

        projects = [Project(self._json(self.get(node_url)), self.session) for node_url in node_urls]
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

    def create_project(self, title):
        """
        Create a project for this user.
        """
        project_payload = {
            "data": {
                "type": "nodes",
                "attributes": {
                    "title": title,
                    "category": "project"
                }
            }
        }
        response = self.post(self.session.build_url('nodes'),
                             data=json.dumps(project_payload),
                             headers={'content-type': 'application/json'})

        if response.status_code == 201:
            return self.project(response.json()['data']['id'])
        else:
            raise PresQTResponseException(
                "Response has status code {} while creating project {}".format(response.status_code,
                                                                               title),
                status.HTTP_400_BAD_REQUEST)