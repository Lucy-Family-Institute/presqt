import json


def read_file(file_path, is_json=False):
    """
    Read a file.

    Parameters
    ----------
    file_path : str
        Path that the file should be read from.
    is_json : boolean
        Flag representing if the file should is JSON.
    """
    if is_json:
        with open(file_path, 'r') as metadata_file:
            return json.load(metadata_file)
    else:
        return open(file_path, 'rb').read()
