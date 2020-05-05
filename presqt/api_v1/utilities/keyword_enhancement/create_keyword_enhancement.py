import json


def create_keyword_enhancement(self, resource):
    # if this is the PresQT Keyword Enhancement file, don't write it to disk but get its contents
    if resource['title'] == 'PRESQT_KEYWORD_ENHANCEMENTS.json':
        source_keyword_enhancement_content = json.loads(resource['file'].decode())
        # If the keyword enhancement is valid then grab its contents and don't save it
        # TODO: Validate
        if True:
            self.source_keyword_enhancement = self.source_keyword_enhancement + \
                                              source_keyword_enhancement_content['enhancements']
            self.source_main_keywords = self.source_main_keywords + \
                                        source_keyword_enhancement_content['mainKeywords']
            return True
        # If the keyword enhancement is invalid rename and write it. We don't want invalid contents.
        else:
            resource['path'] = resource['path'].replace('PRESQT_KEYWORD_ENHANCEMENTS.json',
                                                        'INVALID_PRESQT_KEYWORD_ENHANCEMENTS.json')

    return