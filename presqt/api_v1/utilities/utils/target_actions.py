
from django.urls import reverse

from presqt.api_v1.utilities import read_file


def action_checker(target_name):
    """
    Checks in on targets.json and determines what actions are available for the requesting target.

    Parameters
    ----------
    target_name: str

    Returns
    -------
    A list of available actions for the target.
    """
    target_json = read_file('presqt/targets.json', is_json=True)
    for target in target_json:
        if target['name'] == target_name:
            resource_collection = target['supported_actions']['resource_collection']
            resource_detail = target['supported_actions']['resource_detail']
            resource_download = target['supported_actions']['resource_download']
            resource_upload = target['supported_actions']['resource_upload']
            break

    list_of_actions = []
    if resource_collection is True:
        list_of_actions.append('resource_collection')
    if resource_detail is True:
        list_of_actions.append('resource_detail')
    if resource_download is True:
        list_of_actions.append('resource_download')
    if resource_upload is True:
        list_of_actions.append('resource_upload')

    return list_of_actions


def link_builder(self, instance, list_of_actions, endpoint):
    """
    """
    resource_links = []
    resource_collection_links = []

    if endpoint == 'targets':
        reversed_target_detail = reverse(
            'target', kwargs={'target_name': instance['name']})
        targets_links = [{"name": 'Detail', "link": self.context['request'].build_absolute_uri(
            reversed_target_detail), "method": "GET"}]
        return targets_links

    if endpoint == 'target':
        reversed_collection = reverse('resource_collection', kwargs={
            'target_name': instance['name']})
        target_links = [{"name": "Collection", "link": self.context['request'].build_absolute_uri(
            reversed_collection), "method": "GET"}]
        return target_links

    for action in list_of_actions:
        if action == 'resource_detail':
            reversed_detail = reverse(
                viewname='resource',
                kwargs={'target_name': self.context.get('target_name'),
                        'resource_id': instance['id']})
            resource_collection_links.append({
                "name": "Detail", "link": self.context['request'].build_absolute_uri(
                    reversed_detail), "method": "GET"})

        if action == 'resource_download':
            reversed_download = reverse(
                viewname='resource',
                kwargs={'target_name': self.context.get('target_name'),
                        'resource_id': instance['id'], 'resource_format': 'zip'})
            link_data = {"name": "Download", "link": self.context['request'].build_absolute_uri(
                reversed_download), "method": "GET"}
            resource_links.append(link_data)
            resource_collection_links.append(link_data)

        if action == 'resource_upload':
            if instance['kind'] == 'container':
                reversed_upload = reverse(
                    viewname='resource',
                    kwargs={'target_name': self.context.get('target_name'),
                            'resource_id': instance['id']})
                link_data = {"name": "Upload", "link": self.context['request'].build_absolute_uri(
                    reversed_upload), "method": "POST"}
                resource_links.append(link_data)
                resource_collection_links.append(link_data)

    if endpoint == 'resource':
        return resource_links

    if endpoint == 'resource_collection':
        return resource_collection_links
