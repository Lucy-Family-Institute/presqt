import multiprocessing

from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.utilities import write_file


def spawn_action_process(self, method_to_call):
    """
    Spawn a separate process on the Python kernel to run independently of the
    main request thread. This also starts a watch dog to supervise the spawned process.

    Parameters
    ----------
    self: class
        Class the spawned off method is attached to
    method_to_call: class method
        Method to spawn
    """
    # Create a shared memory map that the watchdog monitors to see if the spawned
    # off process has finished
    self.process_state = multiprocessing.Value('b', 0)

    # Spawn job separate from request memory thread
    function_process = multiprocessing.Process(target=method_to_call)
    # Add the process obj to the base class so we can write the process id in the target function
    self.function_process = function_process
    function_process.start()

    # Start the watchdog process that will monitor the spawned off process
    watch_dog = multiprocessing.Process(target=process_watchdog,
                                        args=[function_process, self.process_info_path,
                                              3600, self.process_state])
    watch_dog.start()
