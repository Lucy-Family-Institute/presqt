import os

from presqt.utilities import read_file


def multiple_process_check(process_info_path):
    """
    """
    # Check if the file exists
    if os.path.exists(process_info_path):
        # Check if this user currently has any other process in progress
        process_info_data = read_file("{}/process_info.json".format(process_info_path), True)

        for key, value in process_info_data.items():
            if value['status'] == 'in_progress':
                return True
        else:
            return False

    return False
