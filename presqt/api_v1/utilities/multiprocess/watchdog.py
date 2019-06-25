from time import sleep

from presqt.api_v1.utilities import write_file
from presqt.api_v1.utilities.io.read_file import read_file


def process_watchdog(process_function, process_info_path, process_time, process_state):
    """
    Watchdog for file transfer processes spawned off using Multiprocessing. It will monitor if the
    process has either finished or has gone over it's processing time.

    Parameters
    ----------
    process_function : class
        Multiprocessing class that we are monitoring
    process_info_path : str
        Path to the process_info.json file for the process running
    process_time : int
        Amount of seconds we want the watchdog to the let the monitored process run
    process_state : class
        Memory map that the spawned off process will update. 'value' attribute will be either 0 or 1
    Returns
    -------

    """
    slept_time = 0
    while slept_time <= process_time:
        sleep(1)
        # If the monitored process has finished
        if process_state.value == 1:
            return
        slept_time += 1

    # If we've reached here then the process reached our time limit and we need to terminate
    # the monitored process and update the process_info.json file.
    process_function.terminate()
    d = read_file(process_info_path, True)
    d['status'] = 'failed'
    d['message'] = 'The process took too long on the server.'
    d['status_code'] = 504
    write_file(process_info_path, d, True)
