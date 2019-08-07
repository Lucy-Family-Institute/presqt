
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

    endpoint: str
        The endpoint that is making the request.

    Returns
    -------
    Returns an array of links.
    """
    links = []

    for action in list_of_actions:
        if action == 'resource_detail':
            reversed_detail = reverse(
                viewname='resource',
                kwargs={'target_name': self.context.get('target_name'),
                        'resource_id': instance['id']})
            links.append({"name": "Detail", "link": self.context['request'].build_absolute_uri(
                reversed_detail), "method": "GET"})

        if action == 'resource_download':
            reversed_download = reverse(
                viewname='resource',
                kwargs={'target_name': self.context.get('target_name'),
                        'resource_id': instance['id'], 'resource_format': 'zip'})
            links.append({"name": "Download", "link": self.context['request'].build_absolute_uri(
                reversed_download), "method": "GET"})

        if action == 'resource_upload':
            if instance['kind'] == 'container':
                reversed_upload = reverse(
                    viewname='resource',
                    kwargs={'target_name': self.context.get('target_name'),
                            'resource_id': instance['id']})
                links.append({"name": "Upload", "link": self.context['request'].build_absolute_uri(
                    reversed_upload), "method": "POST"})
    return links
