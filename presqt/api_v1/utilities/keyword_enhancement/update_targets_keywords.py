from uuid import uuid4

from django.utils import timezone

from presqt.api_v1.utilities import FunctionRouter
from presqt.utilities import PresQTResponseException


def update_targets_keywords(self, project_id):
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
            'allEnhancedKeywords': self.all_keywords,
            'actions': [
                {
                    'id': str(uuid4()),
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