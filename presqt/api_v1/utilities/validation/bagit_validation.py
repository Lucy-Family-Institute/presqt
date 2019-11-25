import bagit
from rest_framework import status

from presqt.utilities import PresQTValidationError


def validate_bag(bag):
    """
    Validate that a bag is in the correct format, all checksums match, and that there
    are no unexpected or missing files

    Parameters
    ----------
    bag : bagit.Bag
        The BagIt class we want to validate.
    """
    # Verify that checksums still match and that there are no unexpected or missing files
    try:
        bag.validate()
    except bagit.BagValidationError as e:
        if e.details:
            if isinstance(e.details[0], bagit.ChecksumMismatch):
                raise PresQTValidationError("Checksums failed to validate.",
                                            status.HTTP_400_BAD_REQUEST)
            else:
                raise PresQTValidationError(str(e.details[0]), status.HTTP_400_BAD_REQUEST)
        else:
            raise PresQTValidationError(str(e), status.HTTP_400_BAD_REQUEST)