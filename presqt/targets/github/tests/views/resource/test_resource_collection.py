import json
import requests
import shutil
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import GITHUB_TEST_USER_TOKEN
from presqt.targets.github.functions.upload_metadata import github_upload_metadata
from presqt.targets.github.utilities import delete_github_repo
from presqt.targets.utilities import shared_upload_function_github
from presqt.utilities import read_file, PresQTError
from presqt.api_v1.utilities import hash_tokens


class TestResourceCollection(SimpleTestCase):
    """
    Test the 'api_v1/targets/github/resources' endpoint's GET method.

    Testing GitHub integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}

    def test_success_github(self):
        """
        Return a 200 if the GET method is successful when grabbing GitHub resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))
            self.assertEqual(len(data['links']), 1)

    def test_success_github_page_2(self):
        """
        Return a 200 if the GET method is successful when grabbing GitHub resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = self.client.get(url + "?page=2", **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))
            self.assertEqual(len(data['links']), 1)

    def test_success_github_with_search(self):
        """
        Return a 200 if the GET method is successful when grabbing GitHub resources with search 
        parameters.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = self.client.get(url + '?title=automated+nhl+goal+light&page=1', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

        ###### Search by ID #######
        response = self.client.get(url + '?id=1296269', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

        #### Search by Author ####
        response = self.client.get(url + '?author=eikonomega&page=1', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

        ### Search by General ###
        response = self.client.get(url + '?general=egg&page=2', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

        # Search by Keywords
        response = self.client.get(url + "?keywords=egg", **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

    def test_error_400_missing_token_github(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})

    def test_error_401_invalid_token_github(self):
        """
        Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'eggyboi'}
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = client.get(url, **header)
        # Verify the error status code and message.
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

    def test_error_400_bad_search_parameters(self):
        """
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        # TOO MANY KEYS
        response = self.client.get(url + '?title=hat&spaghetti=egg&banana=TRUE', **self.header)

        self.assertEqual(response.data['error'],
                         'PresQT Error: The search query is not formatted correctly.')
        self.assertEqual(response.status_code, 400)

        # BAD KEY
        response = self.client.get(url + '?spaghetti=egg', **self.header)

        self.assertEqual(
            response.data['error'], 'PresQT Error: GitHub does not support spaghetti as a search parameter.')
        self.assertEqual(response.status_code, 400)

        # SPECIAL CHARACTERS IN REQUEST
        response = self.client.get(url + '?title=egg:boi', **self.header)

        self.assertEqual(response.data['error'],
                         'PresQT Error: The search query is not formatted correctly.')
        self.assertEqual(response.status_code, 400)

    def test_successful_search_with_no_results(self):
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        # NO AUTHOR FOUND
        response = self.client.get(
            url + '?author=378rFDsahfojIO2QDJOgibberishauthor', **self.header)
        self.assertEqual(response.data['resources'], [])

        # NO ID FOUND
        response = self.client.get(url + '?id=248593331', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resources'], [])


class TestResourceCollectionPOST(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing GitHub integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = GITHUB_TEST_USER_TOKEN
        self.ticket_number = hash_tokens(self.token)
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        self.repo_title = 'NewProject'

        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'github'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.failed_fixity = [
            '/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        self.resources_updated = []
        self.hash_algorithm = 'md5'
        self.process_message = "Upload successful. Fixity can't be determined because GitHub may not have provided a file checksum. See PRESQT_FTS_METADATA.json for more details."

    def tearDown(self):
        """
        This should run at the end of this test class
        """
        delete_github_repo('presqt-test-user', self.repo_title,
                           {'Authorization': 'token {}'.format(GITHUB_TEST_USER_TOKEN)})

    def test_success_202_upload(self):
        """
        Return a 202 when a file is uploading.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_github(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        repo_name_list = [repo['title'] for repo in response_json['resources']]
        self.assertIn(self.repo_title, repo_name_list)
        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_success_202_empty_folder(self):
        """
        If an empty directory is included in the uploaded project, we want to ensure the user is
        made aware.
        """
        bag_with_empty_directory = 'presqt/api_v1/tests/resources/upload/Empty_Directory_Bag.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bag_with_empty_directory, 'rb')},
                                    **self.headers)

        ticket_number = hash_tokens(self.token)
        ticket_path = 'mediafiles/jobs/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)

        # Verify status code and message
        self.assertEqual(upload_job_response.data['resources_ignored'], ['/Egg/Empty_Folder'])

        delete_github_repo('presqt-test-user', 'Egg',
                           {'Authorization': 'token {}'.format(GITHUB_TEST_USER_TOKEN)})
        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_handle_repo_duplication(self):
        """
        If a repo with this name already exists for the user, PresQT should handle repo duplication.
        """
        # What the new repo should be named
        duplicate_title = "{}-PresQT1-".format(self.repo_title)
        second_duplicate_title = "{}-PresQT2-".format(self.repo_title)
        # 202 when uploading a new top level repo
        shared_upload_function_github(self)

        # Verify the duplicate repo does not exist on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        repo_name_list = [repo['title'] for repo in response_json['resources']]
        self.assertNotIn(duplicate_title, repo_name_list)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # Make the second post attempt
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        updated_response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        updated_repo_name_list = [repo['title'] for repo in updated_response_json['resources']]
        self.assertIn(duplicate_title, updated_repo_name_list)

        # Delete upload folder
        shutil.rmtree(ticket_path)

        # Make the third post attempt
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        more_updated_response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        another_updated_repo_name_list = [repo['title']
                                          for repo in more_updated_response_json['resources']]
        self.assertIn(second_duplicate_title, another_updated_repo_name_list)

        delete_github_repo('presqt-test-user', duplicate_title,
                           {'Authorization': 'token {}'.format(self.token)})
        delete_github_repo('presqt-test-user', second_duplicate_title,
                           {'Authorization': 'token {}'.format(self.token)})
        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_presqt_fts_metadata(self):
        """
        Check that the PRESQT_FTS_METADATA is created and what we expect.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_github(self)
        header = {"Authorization": "token {}".format(self.token)}

        # On the project that was just created, we need to get the contents of the metadata file.
        metadata_link = 'https://raw.githubusercontent.com/presqt-test-user/{}/master/PRESQT_FTS_METADATA.json'.format(
            self.repo_title)

        # Get the metadata json
        response = requests.get(metadata_link, headers=header)
        metadata_file = json.loads(response.content)

        # Action metadata
        self.assertEqual(metadata_file['actions'][0]['actionType'], 'resource_upload')
        self.assertEqual(metadata_file['actions'][0]['sourceTargetName'], 'Local Machine')
        self.assertEqual(metadata_file['actions'][0]['destinationTargetName'], 'github')
        self.assertEqual(metadata_file['actions'][0]['destinationUsername'], 'presqt-test-user')

        # File metadata
        self.assertEqual(metadata_file['actions'][0]['files']['created'][0]['title'],
                         'Screen Shot 2019-07-15 at 3.26.49 PM.png')
        self.assertEqual(metadata_file['actions'][0]['files']['created'][0]['sourcePath'],
                         '/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png')
        self.assertEqual(metadata_file['actions'][0]['files']['created'][0]['destinationPath'],
                         '/NewProject/funnyfunnyimages/Screen_Shot_2019-07-15_at_3.26.49_PM.png')
        self.assertEqual(metadata_file['actions'][0]['files']['created'][0]['destinationHashes'],
                         {})

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_bad_metadata_request(self):
        """
        Ensure that the proper error is raised when we get a non-201 response from GitHub.
        """
        # Calling this function manually to confirm explicit error is raised.
        self.assertRaises(PresQTError, github_upload_metadata, self.token, "BAD", {"fake": "data"},)

    def test_upload_with_invalid_metadata_file_and_valid_metadata(self):
        """
        If the upload file contains an invalid metadata file, it needs to be renamed and a new metadata
        file is to be made. If it is valid, we need to append the new action.
        """
        header = {"Authorization": "token {}".format(self.token)}
        bag_with_bad_metadata = 'presqt/api_v1/tests/resources/upload/Invalid_Metadata_Upload.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bag_with_bad_metadata, 'rb')},
                                    **self.headers)

        ticket_number = hash_tokens(self.token)
        ticket_path = 'mediafiles/jobs/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # On the project that was just created, we need to get the contents of the metadata file.
        invalid_metadata_link = 'https://raw.githubusercontent.com/presqt-test-user/Bad_Egg/master/INVALID_PRESQT_FTS_METADATA.json'
        # Get the invalid metadata json
        response = requests.get(invalid_metadata_link, headers=header)
        invalid_metadata_file = json.loads(response.content)

        self.assertEqual(invalid_metadata_file, {'invalid_metadata': 'no bueno'})

        delete_github_repo('presqt-test-user', 'Bad_Egg', header)
        # Delete upload folder
        shutil.rmtree(ticket_path)

        ###### VALID METADATA #######
        bag_with_good_metadata = 'presqt/api_v1/tests/resources/upload/Valid_Metadata_Upload.zip'
        response = self.client.post(self.url, {'presqt-file': open(bag_with_good_metadata, 'rb')},
                                    **self.headers)
        ticket_number = hash_tokens(self.token)
        ticket_path = 'mediafiles/jobs/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        # On the project that was just created, we need to get the contents of the metadata file.
        valid_metadata_link = 'https://raw.githubusercontent.com/presqt-test-user/Good_Egg/master/PRESQT_FTS_METADATA.json'
        # Get the invalid metadata json
        response = requests.get(valid_metadata_link, headers=header)
        valid_metadata_file = json.loads(response.content)

        self.assertEqual(len(valid_metadata_file['actions']), 1)

        delete_github_repo('presqt-test-user', 'Good_Egg', header)
        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_401_unauthorized_user(self):
        """
        If a user does not have a valid GitHub API token, we should return a 401 unauthorized status.
        """
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': 'eggyboi',
                   'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **headers)

        ticket_number = hash_tokens('eggyboi')
        ticket_path = 'mediafiles/jobs/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 401)
        self.assertEqual(upload_job_response.data['message'],
                         'Token is invalid. Response returned a 401 status code.')

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_400_bad_bag_format(self):
        """
        Test that we get 400 bad request status' when the bag to upload is not formatted correctly.
        """
        # First test is of multiple directories
        bad_bag = 'presqt/api_v1/tests/resources/upload/BadProjectMultipleFolders.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bad_bag, 'rb')}, **self.headers)

        ticket_number = hash_tokens(self.token)
        ticket_path = 'mediafiles/jobs/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         'PresQT Error: Repository is not formatted correctly. Multiple directories exist at the top level.')

        # Delete the upload folder
        shutil.rmtree(ticket_path)

        # Files at top level test
        # First test is of multiple directories
        bad_bag = 'presqt/api_v1/tests/resources/upload/SingleFileDuplicate.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bad_bag, 'rb')}, **self.headers)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         'PresQT Error: Repository is not formatted correctly. Files exist at the top level.')

        # Delete the upload folder
        shutil.rmtree(ticket_path)

    def test_500_server_error(self):
        """
        If GitHub is having server issues, we want to make the user aware.
        """
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        with patch('requests.post') as fake_post:
            fake_post.return_value = mock_req

            self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
            response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')},
                                        **self.headers)

            ticket_number = hash_tokens(self.token)
            ticket_path = 'mediafiles/jobs/{}'.format(ticket_number)

            # Wait until the spawned off process finishes in the background
            # to do validation on the resulting files
            process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            while process_info['resource_upload']['status'] == 'in_progress':
                try:
                    process_info = read_file('{}/process_info.json'.format(ticket_path), True)
                except json.decoder.JSONDecodeError:
                    # Pass while the process_info file is being written to
                    pass

            upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
            self.assertEqual(upload_job_response.data['status_code'], 400)
            self.assertEqual(upload_job_response.data['message'],
                             'Response has status code 500 while creating repository {}'.format(
                                 self.repo_title))

            # Delete the upload folder
            shutil.rmtree(ticket_path)
