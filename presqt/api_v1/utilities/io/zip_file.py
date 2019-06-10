import os
import zipfile


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