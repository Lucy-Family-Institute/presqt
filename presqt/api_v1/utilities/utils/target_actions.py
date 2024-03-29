
from django.urls import reverse

from presqt.api_v1.utilities import get_target_data


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
    target_json = get_target_data(target_name)
    supported_actions = target_json['supported_actions']

    return [action for action, boolean in supported_actions.items() if boolean is True]


def link_builder(self, instance, list_of_actions):
    """
    Builds links to be displayed on the API.

    Parameters
    ----------
    instance: instance
        The Resource Obj instance.

    list_of_actions: list
        The list of actions available for the target.

    Returns
    -------
    Returns an array of links.
    """
    links = []

    try:
        instance_id = str(instance['id'])
    except KeyError:
        instance_id = None

    if self.context.get('target_name') in ['github', 'gitlab']:
        instance_id = instance_id.replace('%252E', '%2E').replace('%252F', '%2F')

    for action in list_of_actions:
        if action == 'resource_collection':
            reversed_collection = reverse(
                viewname='resource_collection',
                kwargs={'target_name': instance['name']})
            links.append({"name": "Collection", "link": self.context['request'].build_absolute_uri(
                reversed_collection), "method": "GET"})

        elif action == 'resource_detail':
            reversed_detail = reverse(
                viewname='resource',
                kwargs={'target_name': self.context.get('target_name'),
                        'resource_id': instance_id})
            links.append({"name": "Detail", "link": self.context['request'].build_absolute_uri(
                reversed_detail), "method": "GET"})

        elif action == 'resource_download':
            reversed_download = reverse(
                viewname='resource',
                kwargs={'target_name': self.context.get('target_name'),
                        'resource_id': instance_id, 'resource_format': 'zip'})
            links.append({"name": "Download", "link": self.context['request'].build_absolute_uri(
                reversed_download), "method": "GET"})

        elif action == 'resource_upload':
            try:
                kind = instance['kind']
            except KeyError:
                reversed_upload = reverse(
                    viewname='resource_collection',
                    kwargs={'target_name': instance['name']})
                links.append({"name": "Upload", "link": self.context['request'].build_absolute_uri(
                    reversed_upload), "method": "POST"})
            else:
                if kind == 'container':
                    reversed_upload = reverse(
                        viewname='resource',
                        kwargs={'target_name': self.context.get('target_name'),
                                'resource_id': instance_id})
                    links.append({"name": "Upload", "link": self.context['request'].build_absolute_uri(
                        reversed_upload), "method": "POST"})

        elif action == 'resource_transfer_in':
            try:
                kind = instance['kind']
            except KeyError:
                reversed_transfer = reverse(
                    viewname='resource_collection',
                    kwargs={'target_name': instance['name']})
                links.append({"name": "Transfer", "link": self.context['request'].build_absolute_uri(
                    reversed_transfer), "method": "POST"})
            else:
                if kind == 'container':
                    reversed_transfer = reverse(
                        viewname='resource',
                        kwargs={'target_name': self.context.get('target_name'),
                                'resource_id': instance_id})
                    links.append({"name": "Transfer", "link": self.context['request'].build_absolute_uri(
                        reversed_transfer), "method": "POST"})

    return links
