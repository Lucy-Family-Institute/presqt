import importlib
import inspect
import os
from os import path


class FunctionRouter(object):
    """
    This class acts as a router to allow dynamic function calls based on a given variable.

    Each attribute links to a function. Naming conventions are important. They must match the keys
    we keep in the target.json config file. They are as follows:

    Target Resources Collection:
        {target_name}_resource_collection

    Target Resource Detail:
        {target_name}_resource_detail

    Target Resource Download:
        {target_name}_resource_download

    Target Resource Upload:
        {target_name}_resource_upload

    """
    __lookup_table = {}

    @classmethod
    def _load_lookup_table(cls):
        import presqt.targets
        targets_dir = path.dirname(inspect.getfile(presqt.targets))
        for target_name in os.listdir(path.join(targets_dir)):

            # checking for target_name.functions filters out '__pycache__', '__init__.py', and 'utilities'
            try:
                importlib.import_module('presqt.targets.{}.functions'.format(target_name))
            except ModuleNotFoundError:
                continue

            temp = {}
            try:
                fetch = importlib.import_module('presqt.targets.{}.functions.fetch'.format(target_name))
                temp['resource_collection'] = getattr(fetch, target_name + '_fetch_resources')
            except (ModuleNotFoundError, AttributeError):
                pass
            try:
                fetch = importlib.import_module('presqt.targets.{}.functions.fetch'.format(target_name))
                temp['resource_detail'] = getattr(fetch, target_name + '_fetch_resource')
            except (ModuleNotFoundError, AttributeError):
                pass
            try:
                download = importlib.import_module('presqt.targets.{}.functions.download'.format(target_name))
                temp['resource_download'] = getattr(download, target_name + '_download_resource')
            except (ModuleNotFoundError, AttributeError):
                pass
            try:
                upload = importlib.import_module('presqt.targets.{}.functions.upload'.format(target_name))
                temp['resource_upload'] = getattr(upload, target_name + '_upload_resource')
            except (ModuleNotFoundError, AttributeError):
                pass

            cls.__lookup_table[target_name] = temp


    @classmethod
    def get_function(cls, target_name, action):
        """
        Extracts the getattr() function call to this class method so the code using this class
        is easier to work with.
        """
        return FunctionRouter.__lookup_table[target_name][action]


FunctionRouter._load_lookup_table()