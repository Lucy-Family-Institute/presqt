import json

from presqt.utilities import read_file


def process_wait(process_info, ticket_path):
    # Wait until the spawned off process finishes in the background to do further validation
    while process_info['resource_upload']['status'] == 'in_progress':
        try:
            process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        except json.decoder.JSONDecodeError:
            # Pass while the process_info file is being written to
            pass


def shared_upload_function_osf(test_case_instance):
    test_case_instance.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = test_case_instance.duplicate_action

    # Verify the status code and content
    response = test_case_instance.client.post(test_case_instance.url, {
        'presqt-file': open(test_case_instance.file, 'rb')}, **test_case_instance.headers)

    test_case_instance.ticket_path = 'mediafiles/jobs/{}'.format(test_case_instance.ticket_number)


    # Verify status code and message
    test_case_instance.assertEqual(response.status_code, 202)

    test_case_instance.assertEqual(
        response.data['message'], 'The server is processing the request.')

    # Verify process_info file status is 'in_progress' initially
    process_info = read_file('{}/process_info.json'.format(test_case_instance.ticket_path), True)
    test_case_instance.assertEqual(process_info['resource_upload']['status'], 'in_progress')

    # Wait until the spawned off process finishes in the background to do further validation
    process_wait(process_info, test_case_instance.ticket_path)

    # Verify process_info.json file data
    process_info = read_file('{}/process_info.json'.format(test_case_instance.ticket_path), True)
    test_case_instance.assertEqual(process_info['resource_upload']['status'], 'finished')
    test_case_instance.assertEqual(process_info['resource_upload']['message'], 'Upload successful.')
    test_case_instance.assertEqual(process_info['resource_upload']['status_code'], '200')
    test_case_instance.assertEqual(process_info['resource_upload']['failed_fixity'], [])
    test_case_instance.assertEqual(
        process_info['resource_upload']['resources_ignored'], test_case_instance.resources_ignored)
    test_case_instance.assertEqual(
        process_info['resource_upload']['resources_updated'], test_case_instance.resources_updated)
    test_case_instance.assertEqual(
        process_info['resource_upload']['hash_algorithm'], test_case_instance.hash_algorithm)


def shared_upload_function_github(test_case_instance):
    test_case_instance.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = test_case_instance.duplicate_action
    response = test_case_instance.client.post(test_case_instance.url, {'presqt-file': open(
        test_case_instance.file, 'rb')}, **test_case_instance.headers)

    test_case_instance.ticket_path = 'mediafiles/jobs/{}'.format(test_case_instance.ticket_number)

    # Verify status code and message
    test_case_instance.assertEqual(response.status_code, 202)
    test_case_instance.assertEqual(
        response.data['message'], 'The server is processing the request.')

    # Verify process_info file status is 'in_progress' initially
    process_info = read_file('{}/process_info.json'.format(test_case_instance.ticket_path), True)
    test_case_instance.assertEqual(process_info['resource_upload']['status'], 'in_progress')

    # Wait until the spawned off process finishes in the background to do further validation
    process_wait(process_info, test_case_instance.ticket_path)

    # Verify process_info.json file data
    process_info = read_file('{}/process_info.json'.format(test_case_instance.ticket_path), True)

    test_case_instance.assertEqual(process_info['resource_upload']['status'], 'finished')
    test_case_instance.assertEqual(
        process_info['resource_upload']['message'], test_case_instance.process_message)
    test_case_instance.assertEqual(process_info['resource_upload']['status_code'], '200')
    test_case_instance.assertEqual(
        process_info['resource_upload']['failed_fixity'], test_case_instance.failed_fixity)
    test_case_instance.assertEqual(
        process_info['resource_upload']['resources_ignored'], test_case_instance.resources_ignored)
    test_case_instance.assertEqual(
        process_info['resource_upload']['resources_updated'], test_case_instance.resources_updated)
    test_case_instance.assertEqual(
        process_info['resource_upload']['hash_algorithm'], test_case_instance.hash_algorithm)


def shared_upload_function_gitlab(test_case_instance):
    test_case_instance.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = test_case_instance.duplicate_action
    response = test_case_instance.client.post(test_case_instance.url, {'presqt-file': open(
        test_case_instance.file, 'rb')}, **test_case_instance.headers)

    test_case_instance.ticket_path = 'mediafiles/jobs/{}'.format(test_case_instance.ticket_number)

    # Verify status code and message
    test_case_instance.assertEqual(response.status_code, 202)
    test_case_instance.assertEqual(
        response.data['message'], 'The server is processing the request.')

    # Verify process_info file status is 'in_progress' initially
    process_info = read_file('{}/process_info.json'.format(test_case_instance.ticket_path), True)
    test_case_instance.assertEqual(process_info['resource_upload']['status'], 'in_progress')

    # Wait until the spawned off process finishes in the background to do further validation
    process_wait(process_info, test_case_instance.ticket_path)

    # Verify process_info.json file data
    process_info = read_file('{}/process_info.json'.format(test_case_instance.ticket_path), True)
    test_case_instance.assertEqual(process_info['resource_upload']['status'], 'finished')
    test_case_instance.assertEqual(process_info['resource_upload']['message'], test_case_instance.success_message)
    test_case_instance.assertEqual(process_info['resource_upload']['status_code'], '200')
    test_case_instance.assertEqual(process_info['resource_upload']['failed_fixity'], [])
    test_case_instance.assertEqual(
        process_info['resource_upload']['resources_ignored'], test_case_instance.resources_ignored)
    test_case_instance.assertEqual(
        process_info['resource_upload']['resources_updated'], test_case_instance.resources_updated)
    test_case_instance.assertEqual(
        process_info['resource_upload']['hash_algorithm'], test_case_instance.hash_algorithm)
