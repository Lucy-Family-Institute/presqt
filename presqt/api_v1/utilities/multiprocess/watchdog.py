import json
from time import sleep

from presqt.utilities import read_file, write_file


def process_watchdog(function_process, process_info_path, process_time, action):
    """
    Monitoring function for the file transfer processes spawned off using Multiprocessing.
    It will monitor if the process has either finished or has gone over it's processing time.

    Parameters
    ----------
    function_process : multiprocessing.Process
        Multiprocessing class that we are monitoring
    process_info_path : str
        Path to the process_info.json file for the process running
    process_time : int
        Amount of seconds we want the watchdog to the let the monitored process run
    """
    slept_time = 0
    while slept_time <= process_time:
        sleep(1)

        # Get the contents of process_info.json.
        # While loop is required in case the json file is being written to while being read.
        process_info_data = None
        while process_info_data is None:
            try:
                process_info_data = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
            # Exception is mostly in place for testing
            except FileNotFoundError:
                return

        # If the monitored process has finished
        if process_info_data[action]['status'] != 'in_progress':
            return
        slept_time += 1

    # If we've reached here then the process reached our time limit and we need to terminate
    # the monitored process and update the process_info.json file.
    function_process.terminate()
    process_info_data[action]['status'] = 'failed'
    process_info_data[action]['message'] = 'The process took too long on the server.'
    process_info_data[action]['status_code'] = 504
    write_file(process_info_path, process_info_data, True)
