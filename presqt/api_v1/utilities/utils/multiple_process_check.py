import os

from presqt.utilities import read_file


def multiple_process_check(process_info_path):
    """
    Check in on if a user currrently has an action in progress.

    Parameters
    ----------
    process_info_path: str
        The path to the user's action contents

    Returns
    -------
        Whether the user has an action in progress or not (bool)
    """
    process_info_file = "{}/process_info.json".format(process_info_path)
    # Check if the file exists
    if os.path.exists(process_info_file):
        # Check if this user currently has any other process in progress
        process_info_data = read_file(process_info_file, True)
        # Loop through the dictionaries and check the status's
        for key, value in process_info_data.items():
            if value['status'] == 'in_progress':
                return True
    # Nothing in progress
    return False
