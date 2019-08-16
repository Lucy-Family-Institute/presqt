import json

import requests
from rest_framework import status

from presqt.utilities import (PresQTResponseException, PresQTInvalidTokenError,
                              get_dictionary_from_list, list_differences)
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
        Fetch all top level projects for this user.
        """
        url = self.session.build_url('users', 'me', 'nodes')
        response_data = self._follow_next(url)

        projects = [Project({'data': project_json}, self.session) for project_json in response_data]

        project_ids = [project.id for project in projects]
        top_level_project_ids = [project.parent_node for project in projects]
        unique_project_ids = list(set(list_differences(top_level_project_ids, project_ids)))

        # projects = [Project({'data': project_json}, self.session) for project_json in response_data]
        # project_ids = [project.id for project in projects]
        # top_level_project_ids = [project.parent_node for project in projects]
        # unique_project_ids = list(set(list_differences(top_level_project_ids, project_ids)))

        return [project for project in projects if project.parent_node in unique_project_ids]

    def get_user_resources(self):
        """
        Get all of the user's resources. Return in the structure expected for the PresQT API.

        Returns
        -------
        List of all resources.
        """
        resources = []
        user_storages = []

        for project in self.projects():
            resources.append({
                'kind': 'container',
                'kind_name': 'project',
                'id': project.id,
                'container': None,
                'title': project.title
            })

            # Get sub projects

            for storage in project.storages():
                resources.append({
                    'kind': 'container',
                    'kind_name': 'storage',
                    'id': storage.id,
                    'container': project.id,
                    'title': storage.title
                })

                # Keep track of all storage file urls that need to be called.
                user_storages.append(storage._files_url)

        # Asynchronously call all storage file urls to get the storage's top level resources.
        storage_data = self.run_urls_async(user_storages)

        # If a storage has more than 10 resources then they will be paginated. Get all paginated
        # file urls and call them asynchronously.
        children_urls = self._get_follow_next_urls(storage_data)
        storage_data.extend(self.run_urls_async(children_urls))

        # Loop through the storage resources to either add them to the main resources list or
        # traverse further down the tree to get their children resources.
        for resource in storage_data:
            if resource['data']:
                # Calculate the given resource's container_id
                parent_project_id = resource['data'][0]["relationships"]['node']['data']["id"]
                parent_provider = resource['data'][0]['attributes']['provider']
                container_id = '{}:{}'.format(parent_project_id, parent_provider)

                self.get_resources_objects(resource, resources, container_id)
        return resources

    def get_resources_objects(self, resource, resources, container_id):
        """
        Get all resources for this container.
        This exists so we can get all resources in the structure we want for our API payloads.

        Parameters
        ----------
        resource: dict
            The resource who's inner resources we want to get.
        resources: list
            Main list of resources to append each inner resource to. Essentially the API payload.
        container_id: str
            The container ID the resources belong to.
        """
        folder_data = []
        for data in resource['data']:
            kind = data['attributes']['kind']

            if kind == 'file':
                file = File(data, self.session)
                file_obj = {
                    'kind': file.kind,
                    'kind_name': file.kind_name,
                    'id': file.id,
                    'container': container_id,
                    'title': file.title
                }
                resources.append(file_obj)

            elif kind == 'folder':
                folder = Folder(data, self.session)
                folder_obj = {
                    'kind': folder.kind,
                    'kind_name': folder.kind_name,
                    'id': folder.id,
                    'container': container_id,
                    'title': folder.title
                }
                resources.append(folder_obj)

                # Keep track of all folders' file urls that need to be called.
                folder_data.append({'url': folder._files_url,
                                     'id': folder.id,
                                     'path': folder.materialized_path})

        # Asynchronously call all folder file urls to get the folder's top level resources.
        folder_urls = [folder_dict['url'] for folder_dict in folder_data]
        folder_resources = self.run_urls_async(folder_urls)

        # If a folder has more than 10 resources then they will be paginated. Get all paginated
        # file urls and call them asynchronously.
        children_urls = self._get_follow_next_urls(folder_resources)
        folder_resources.extend(self.run_urls_async(children_urls))

        # For each resource, get it's container_id and resources
        for folder_resource in folder_resources:
            resource_attr = folder_resource['data'][0]['attributes']
            parent_path = resource_attr['materialized_path'][:-len(resource_attr['name'])]
            # Find the corresponding parent_path in the folder_data list of dictionaries so we
            # can get the container id for this resource.
            container_id = get_dictionary_from_list(folder_data, 'path', parent_path)['id']
            self.get_resources_objects(folder_resource, resources, container_id)

    def create_project(self, title):
        """-
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