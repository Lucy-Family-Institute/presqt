import json
import os
import shutil
import zipfile

from rest_framework.reverse import reverse

from presqt.utilities import write_file, read_file


def shared_get_success_function_202(test_case_instance):
    """
    This function will be used by tests that successfully hit the resource GET endpoint.
    It uses class attributes that are set in the test methods.

    Parameters
    ----------
    test_case_instance : instance
        instance of a test case

    Returns
    -------
    Fixity JSON from the fixity_info.json file
    """
    url = reverse('resource', kwargs={'target_name': test_case_instance.target_name,
                                      'resource_id': test_case_instance.resource_id,
                                      'resource_format': 'zip'})
    response = test_case_instance.client.get(url, **test_case_instance.header)
    # Verify the status code and content
    test_case_instance.assertEqual(response.status_code, 202)
    test_case_instance.assertEqual(
        response.data['message'], 'The server is processing the request.')
    ticket_number = response.data['ticket_number']
    ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

    # Verify process_info file status is 'in_progress' initially
    process_info = read_file('{}/process_info.json'.format(ticket_path), True)
    test_case_instance.assertEqual(process_info['status'], 'in_progress')

    # Wait until the spawned off process finishes in the background
    # to do validation on the resulting files
    while process_info['status'] == 'in_progress':
        try:
            process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        except json.decoder.JSONDecodeError:
            # Pass while the process_info file is being written to
            pass

    # Verify the final status in the process_info file is 'finished'
    process_info = read_file('{}/process_info.json'.format(ticket_path), True)
    test_case_instance.assertEqual(process_info['status'], 'finished')
    # Verify zip file exists and has the proper amount of resources in it.
    base_name = '{}_download_{}'.format(
        test_case_instance.target_name, test_case_instance.resource_id)
    zip_path = '{}/{}.zip'.format(ticket_path, base_name)
    test_case_instance.zip_file = zipfile.ZipFile(zip_path)
    test_case_instance.assertEqual(os.path.isfile(zip_path), True)
    test_case_instance.assertEqual(len(test_case_instance.zip_file.namelist()), test_case_instance.file_number)

    # Verify that the resource we expect is there.
    test_case_instance.assertEqual(os.path.isfile('{}/{}/data/{}'.format(
        ticket_path, base_name, test_case_instance.file_name)), True)

    # Delete corresponding folder
    shutil.rmtree(ticket_path)

    # Return fixity info JSON
    fixity_file = test_case_instance.zip_file.open('{}/data/fixity_info.json'.format(base_name))
    return json.load(fixity_file)


def shared_get_success_function_202_with_error(test_case_instance):
    """
    This function will be used by tests that successfully hit the GET resource endpoint but
    fail during the Resource._download_resource function.
    It uses class attributes that are set in the test methods.

    Parameters
    ----------
    test_case_instance : instance
        instance of a test case
    """
    url = reverse('resource', kwargs={'target_name': test_case_instance.target_name,
                                      'resource_id': test_case_instance.resource_id,
                                      'resource_format': 'zip'})
    response = test_case_instance.client.get(url, **test_case_instance.header)
    # Verify the status code and content
    test_case_instance.assertEqual(response.status_code, 202)
    test_case_instance.assertEqual(
        response.data['message'], 'The server is processing the request.')
    ticket_number = response.data['ticket_number']
    ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

    # Verify process_info file status is 'in_progress' initially
    process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                             True)
    test_case_instance.assertEqual(process_info['status'], 'in_progress')

    # Wait until the spawned off process finishes in the background
    # to do validation on the resulting files
    while process_info['status'] == 'in_progress':
        try:
            process_info = read_file(
                'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
        except json.decoder.JSONDecodeError:
            # Pass while the process_info file is being written to
            pass

    process_info = read_file('{}/process_info.json'.format(ticket_path), True)

    # Verify that the zip file doesn't exist
    base_name = 'osf_download_{}'.format(test_case_instance.resource_id)
    zip_path = '{}/{}.zip'.format(ticket_path, base_name)
    test_case_instance.assertEqual(os.path.isfile(zip_path), False)

    # Verify the final status in the process_info file is 'failed'
    test_case_instance.assertEqual(process_info['status'], 'failed')
    test_case_instance.assertEqual(process_info['message'], test_case_instance.status_message)
    test_case_instance.assertEqual(process_info['status_code'], test_case_instance.status_code)

    # Delete corresponding folder
    shutil.rmtree(ticket_path)


def shared_call_get_resource_zip(test_case_instance, resource_id):
    """
    Call the resource endpoint first to download the resources.

    Parameters
    ----------
    test_case_instance : instance
        instance of a test case
    resource_id : str
        The id of the resource to be downloaded
    """
    url = reverse('resource', kwargs={'target_name': test_case_instance.target_name,
                                      'resource_id': resource_id,
                                      'resource_format': 'zip'})
    response = test_case_instance.client.get(url, **test_case_instance.header)
    # Verify the status code
    test_case_instance.assertEqual(response.status_code, 202)
    test_case_instance.process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(
        test_case_instance.ticket_number)
    process_info = read_file(test_case_instance.process_info_path, True)

    # Save initial process data that we can use to rewrite to the process_info file for testing
    test_case_instance.initial_process_info = process_info

    # Wait until the spawned off process finishes in the background
    while process_info['resource_download']['status'] == 'in_progress':
        try:
            process_info = read_file(test_case_instance.process_info_path, True)
        except json.decoder.JSONDecodeError:
            # Pass while the process_info file is being written to
            pass
    test_case_instance.assertNotEqual(process_info['resource_download']['status'], 'in_progress')