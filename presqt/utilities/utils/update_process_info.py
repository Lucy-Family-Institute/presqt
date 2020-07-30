from presqt.utilities import write_file, read_file


def update_process_info(process_info_path, total_files):
    """
    Update the process_info.json file with the number of total files involved in the action

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    total_files: int
        Total number of resources involved in the action
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data['total_files'] = total_files
    write_file(process_info_path, process_info_data, True)
    return

def increment_process_info(process_info_path):
    """
    Increment the files_finished attribute in the process_info.json file

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data['files_finished'] = process_info_data['files_finished'] + 1
    write_file(process_info_path, process_info_data, True)
    return