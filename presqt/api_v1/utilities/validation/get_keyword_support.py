from presqt.utilities import read_file


def get_keyword_support(source_target_name, destination_target_name):
    json_data = read_file('presqt/specs/targets.json', True)
    for data in json_data:
        if data['name'] == source_target_name or data['name'] == destination_target_name:
            if not data["supported_actions"]['keywords'] or not data["supported_actions"]['keywords_upload']:
                return False
    return True