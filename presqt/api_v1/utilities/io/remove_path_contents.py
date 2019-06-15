import os
import shutil


def remove_path_contents(path, *file_exceptions):
    """
    Removes all directories and files in a given path. It does not remove the directory root itself.

    Parameters
    ----------
    path : str
        Path of the directory contents we want to remove.
    file_exceptions : tuple
        Variable length argument list of files we don't want to remove from the directory
    """
    for the_file in os.listdir(path):
        file_path = os.path.join(path, the_file)
        if os.path.isfile(file_path) and the_file not in file_exceptions:
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
