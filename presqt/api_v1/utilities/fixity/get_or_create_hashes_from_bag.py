from presqt.api_v1.utilities.fixity.hash_generator import hash_generator
from presqt.api_v1.utilities.utils.get_target_data import get_target_data
from presqt.utilities import read_file


def get_or_create_hashes_from_bag(self, bag):
    """
    Create a hash dictionary to compare with the hashes returned from the target after upload.
    If the destination target supports a hash provided by the bag then use those hashes
    otherwise create new hashes with a target supported hash.

    Parameters
    ----------
    self: class instance
        Instance of the class we are getting the bag for
    bag: BagIt object
        BagIt bag we are getting the files and hashes from

    Returns
    -------
    file_hashes: dict
        Dictionaries of file paths(key) and their hashes (value)
    hash_algorithm: str
        Hash algorithm used to calculate the hashes
    """
    file_hashes = {}

    # Check if the hash algorithms provided in the bag are supported by the target
    target_supported_algorithms = get_target_data(self.destination_target_name)[
        'supported_hash_algorithms']
    matched_algorithms = set(target_supported_algorithms).intersection(bag.algorithms)

    # If the bag and target have a matching supported hash algorithm then pull that algorithm's
    # hash from the bag.
    if matched_algorithms:
        hash_algorithm = matched_algorithms.pop()
        for key, value in bag.payload_entries().items():
            file_hashes['{}/{}'.format(self.resource_main_dir, key)] = value[
                hash_algorithm]

    # Else calculate a new hash for each file with a target supported hash algorithm.
    else:
        try:
            hash_algorithm = target_supported_algorithms[0]
        except IndexError:
            hash_algorithm = 'md5'
        for key, value in bag.payload_entries().items():
            file_path = '{}/{}'.format(self.resource_main_dir, key)
            binary_file = read_file(file_path)
            file_hashes[file_path] = hash_generator(binary_file, hash_algorithm)

    return file_hashes, hash_algorithm