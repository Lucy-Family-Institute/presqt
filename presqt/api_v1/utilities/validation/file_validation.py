import zipfile

from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status

from presqt.utilities import PresQTValidationError


def file_validation(request):
    """
    Verify that the file, 'presqt-file' exists in the body of the request.

    Parameters
    ----------
    request : HTTP request object

    Returns
    -------
    Returns the file provided in the body named 'presqt-file'
    """
    try:
        file = request.FILES['presqt-file']
    except MultiValueDictKeyError:
        raise PresQTValidationError(
            "PresQT Error: The file, 'presqt-file', is not found in the body of the request.",
            status.HTTP_400_BAD_REQUEST)

    # Check if the file provided is a zip file
    if not zipfile.is_zipfile(file):
        raise PresQTValidationError(
            "PresQT Error: The file provided, 'presqt-file', is not a zip file.", status.HTTP_400_BAD_REQUEST)
    return file
