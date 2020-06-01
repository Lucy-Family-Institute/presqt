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
    # Upload enhanced source keywords to destination
    destination_keywords_upload_func = FunctionRouter.get_function(self.destination_target_name, 'keywords_upload')
    try:
        updated_destination_keywords = destination_keywords_upload_func(self.destination_token, project_id, self.all_keywords)
    except PresQTResponseException:
        metadata_succeeded = False

    # Upload enhanced source keywords to source
    source_keywords_upload_func = FunctionRouter.get_function(self.source_target_name, 'keywords_upload')
    try:
        updated_source_keywords = source_keywords_upload_func(self.source_token, self.source_resource_id, self.all_keywords)
    except PresQTResponseException:
        return False
    else:
        # Update/create source FTS metadata file with enhanced keywords
        enhance_dict = {
            'presqtKeywords': self.all_keywords,
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
                    'keywordEnhancements': {
                        'initialKeywords': self.initial_keywords,
                        'enhancedKeywords': self.enhanced_keywords,
                        'enhancer': 'scigraph'

                    },
                    'files': {
                        'created': [],
                        'updated': [],
                        'ignored': []
                    }
                }
            ]
        }

        source_upload_metadata_func = FunctionRouter.get_function(self.source_target_name, 'metadata_upload')
        source_upload_metadata_func(self.source_token, updated_source_keywords['project_id'], enhance_dict)

    return metadata_succeeded


def update_desination_with_source_pre_suggest_keywords(self, project_id):
    """
    Upload keywords to the destination from the source.
    """
    destination_keywords_get_func = FunctionRouter.get_function(self.destination_target_name, 'keywords')
    try:
        initial_keywords = destination_keywords_get_func(self.destination_token, project_id)['keywords']
    except PresQTResponseException:
        initial_keywords = []

    keywords_for_project = self.initial_keywords + initial_keywords
    metadata_succeeded = True
    # Upload initial source keywords to destination
    destination_keywords_upload_func = FunctionRouter.get_function(self.destination_target_name, 'keywords_upload')
    try:
        destination_keywords_upload_func(self.destination_token, project_id, keywords_for_project)
    except PresQTResponseException:
        metadata_succeeded = False

    return metadata_succeeded
