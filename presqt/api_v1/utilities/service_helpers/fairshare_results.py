import json

from presqt.utilities import read_file


def fairshare_results(response_json, test_list):
    """
    Build a list of FAIRshare test results from a given POST response.

    Parameters
    ----------
    response_json : dict
        The dictionary returned by FAIRshare

    Returns
    -------
        A list of dictionaries with result information

    """
    evaluation_results = response_json['evaluationResult']
    evaluation_results_json = json.loads(evaluation_results)
    results_list = []
    fairshare_test_info = read_file("presqt/specs/services/fairshare/fairshare_description_fetch.json",
                                    True)

    # Loop through evaluations and build some dicts
    for metric, results in evaluation_results_json.items():
        # Only return results for the tests specified by the user...
        if fairshare_test_info[metric]['test_name'] in test_list:
            result_dict = {
                'metric_link': metric,
                'test_name': fairshare_test_info[metric]['test_name'],
                'description': fairshare_test_info[metric]['description'],
                'successes': [],
                'failures': [],
                'warnings': []
            }

            results_string = results[0]['http://schema.org/comment'][0]['@value']

            successes = results_string.split('\n')
            for success in successes:
                if not success.isspace() and success != '':
                    if success.startswith('SUCCESS: '):
                        result_dict['successes'].append(success.partition('SUCCESS: ')[2])
                    elif success.startswith('FAILURE: '):
                        result_dict['failures'].append(success.partition('FAILURE: ')[2])
                    elif success.startswith('WARN: '):
                        result_dict['warnings'].append(success.partition('WARN: ')[2])

            # Get rid of duplicate messages
            result_dict['successes'] = list(set(result_dict['successes']))
            result_dict['failures'] = list(set(result_dict['failures']))
            result_dict['warnings'] = list(set(result_dict['warnings']))
            results_list.append(result_dict)

    return results_list
