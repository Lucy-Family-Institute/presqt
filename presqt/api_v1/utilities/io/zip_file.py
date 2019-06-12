import os
import zipfile


def zip_directory(destination_path, source_path, to_strip=None):
    """
    Zip a directory to a specified path.

    Parameters
    ----------
    destination_path : str
        Path to save the zip file
    source_path : str
        Path of the directory to be zipped.
    to_strip : str
        String of the root directory we want to strip from the final root that's zipped up.
    """
    my_zip_file = zipfile.ZipFile(destination_path, "w")
    for root, dirs, files in os.walk(source_path):
        for file in files:
            # Change file path to write to.
            new_path = os.path.join(root, file)[len(to_strip)+1:]
            my_zip_file.write(os.path.join(root, file), new_path)
    my_zip_file.close()