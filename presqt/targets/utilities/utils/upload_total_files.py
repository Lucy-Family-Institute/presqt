import os


def upload_total_files(resource_main_dir):
    """
    This function will return the total number of files to be uploaded to the target.

    Parameters
    ----------
    resource_main_dir: str
        Path to the main directory for the resources to be uploaded.

    Returns
    -------
        The number of files to be uploaded.
    """
    return len([os.path.join(path, name) for path, subdirs, files in os.walk(resource_main_dir) for name in files])
