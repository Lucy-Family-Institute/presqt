import json
import os


def write_file(file_path, contents, is_json=False):
    """
    Write a file to a specified path on disk.

    Parameters
    ----------
    file_path : str
        Path that the file should be saved to.
    contents : bytes or JSON
        Contents to be written to the file.
    is_json : boolean
        Flag representing if the file should be JSON.
    """
    # Create Directory
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # Write file
    if is_json:
        with open(file_path, 'w') as outfile:
            json.dump(contents, outfile)
    else:
        with open(file_path, 'wb') as outfile:
            outfile.write(contents)

    outfile.close()