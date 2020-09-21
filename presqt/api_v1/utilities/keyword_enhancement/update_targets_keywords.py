from uuid import uuid4

from django.utils import timezone

from presqt.api_v1.utilities import FunctionRouter
from presqt.utilities import PresQTResponseException


def update_targets_keywords(self, project_id):
    """
    Upload new enhanced keywords to the destination and source.
    Edit and update/create the source's metadata file with the new keyword enhancements.
    """
    metadata_succeeded = True

    # Get the initial destination keywords, if any
    destination_keywords_get_func = FunctionRouter.get_function(
        self.destination_target_name, 'keywords')

    try:
        destination_initial_keywords = destination_keywords_get_func(
            self.destination_token, project_id)['keywords']
    except PresQTResponseException:
        destination_initial_keywords = []

    # Upload enhanced source keywords to destination
    destination_keywords_upload_func = FunctionRouter.get_function(
        self.destination_target_name, 'keywords_upload')

    try:
        destination_keywords_upload_func(self.destination_token, project_id,
                                         list(set(self.all_keywords + destination_initial_keywords + self.keywords)))
    except PresQTResponseException:
        metadata_succeeded = False

    # Upload enhanced source keywords to source
    source_keywords_upload_func = FunctionRouter.get_function(
        self.source_target_name, 'keywords_upload')

    try:
        updated_source_keywords = source_keywords_upload_func(
            self.source_token, self.source_resource_id, self.enhanced_keywords + self.initial_keywords + self.keywords)
    except PresQTResponseException:
        return False, destination_initial_keywords
    else:
        # Update/create source FTS metadata file with enhanced keywords
        enhance_dict = {
            'allKeywords': self.initial_keywords + self.enhanced_keywords + self.keywords,
            'actions': [
                {
                    'id': str(uuid4()),
                    'details': self.details,
                    'actionDateTime': str(timezone.now()),
                    'actionType': 'transfer_enhancement',
                    'sourceTargetName': self.source_target_name,
                    'sourceUsername': self.source_username,
                    'destinationTargetName': self.source_target_name,
                    'destinationUsername': self.source_username,
                    'keywords': self.keyword_dict,
                    'files': {
                        'created': [],
                        'updated': [],
                        'ignored': []
                    }
                }
            ]
        }

        source_upload_metadata_func = FunctionRouter.get_function(
            self.source_target_name, 'metadata_upload')

        source_upload_metadata_func(
            self.source_token, updated_source_keywords['project_id'], enhance_dict)

    return metadata_succeeded, destination_initial_keywords
