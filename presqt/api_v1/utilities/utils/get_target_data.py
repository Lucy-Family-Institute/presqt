from presqt.utilities import read_file


def get_target_data(target_name):
    """
    Get the data for a given target from targets.json

    Parameters
    ----------
    target_name : str
        The target to get data for

    Returns
    -------
    JSON object of the target data.
    """
    target_data = read_file('presqt/targets.json', True)
    for data in target_data:
        if data['name'] == target_name:
            return data