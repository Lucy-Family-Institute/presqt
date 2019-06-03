import json
import os
import zipfile


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
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if is_json:
        with open(file_path, 'w') as outfile:
            json.dump(contents, outfile)
    else:
        with open(file_path, 'wb') as outfile:
            outfile.write(contents)

def zip_directory(destination_path, source_path):
    """
    Zip a directory to a specified path.

    Parameters
    ----------
    destination_path : str
        Path to save the zip file
    source_path :
        Path of the directory to be zipped.
    """
    my_zip_file = zipfile.ZipFile(destination_path, "w")
    for root, dirs, files in os.walk(source_path):
        for file in files:
            my_zip_file.write(os.path.join(root, file))
    my_zip_file.close()