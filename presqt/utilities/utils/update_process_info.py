# TODO: Refactor these funcs to keep things dry

from presqt.utilities import write_file, read_file


def update_process_info(process_info_path, total_files, action, function):
    """
    Update the process_info.json file with the number of total files involved in the action

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    total_files: int
        Total number of resources involved in the action
    action: str
        The action to update in the process_info.json object
    function: str
        The function being called
    """
    process_info_data = read_file(process_info_path, True)

    # Get the proper dict key
    if function == 'upload':
        key = 'upload_total_files'
    elif function == 'download':
        key = 'download_total_files'
    else:
        key = 'total_files'

    process_info_data[action][key] = total_files
    write_file(process_info_path, process_info_data, True)
    return


def increment_process_info(process_info_path, action, function):
    """
    Increment the download_files_finished attribute in the process_info.json file

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    action: str
        The action to update in the process_info.json object
    function: str
        The function being called
    """
    process_info_data = read_file(process_info_path, True)

    # Get the proper dict key
    if function == 'upload':
            key = 'upload_files_finished'
    elif function == 'download':
        key = 'download_files_finished'
    else:
        key = 'files_finished'

    process_info_data[action][key] = process_info_data[action][key] + 1
    write_file(process_info_path, process_info_data, True)
    return


def update_process_info_message(process_info_path, action, message):
    """
    Update the process_info.json file with the number of total files involved in the action

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    action: str
        The action to update in the process_info.json object
    message: str
        The message to add to the process_info file
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data[action]['message'] = message
    write_file(process_info_path, process_info_data, True)
    return
