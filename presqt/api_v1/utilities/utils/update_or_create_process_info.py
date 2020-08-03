import os

from presqt.utilities import read_file, write_file


def update_or_create_process_info(process_obj, action, ticket_number):
    """
    Create or update the process_info.json file for a job.

    Parameters
    ----------
    process_obj: dict
        Process info dictionary to save in the process_info.json file
    action: str
        The current action which the process_obj will be saved to in the process_info.json file
    ticket_number: str
        Ticket number for user's action and also the name of the directory for process_info.json

    Returns
    -------
    Returns the path to the process_info.json file
    """
    process_info_path = os.path.join('mediafiles', 'jobs', str(ticket_number), 'process_info.json')
    # If there already exists a process_info.json file for this user then add to the process dict
    if os.path.isfile(process_info_path):
        file_obj = read_file(process_info_path, True)
        file_obj[action] = process_obj
    # If no process_info.json file exists for this user than create a new process dict
    else:
        file_obj = {action: process_obj}

    write_file(process_info_path, file_obj, True)
    return process_info_path
