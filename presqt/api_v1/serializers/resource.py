
from rest_framework import serializers
from django.urls import reverse

from presqt.api_v1.utilities import action_checker, link_builder
from presqt.utilities import list_intersection


class ResourcesSerializer(serializers.Serializer):
    """
    Serializer for a given resource object in a target resource list.
    """
    kind = serializers.CharField(max_length=256)
    kind_name = serializers.CharField(max_length=256)
    id = serializers.CharField(max_length=256)
    container = serializers.CharField(max_length=256)
    title = serializers.CharField(max_length=256)
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        """
        Translate the `links` property to a custom array of Hyperlink values.

        Parameters
        ----------
        instance : Target Obj instance

        Returns
        -------
        Hyperlink url for Target detail API endpoint
        """
        list_of_actions = action_checker(self.context.get('target_name'))
        # Build a list of endpoint_actions and compare with list of actions
        resources_actions = list_intersection(list_of_actions, ['resource_detail'])

        links = link_builder(self, instance, resources_actions)

        return links


class ResourceSerializer(serializers.Serializer):
    """
    Serializer for a give resource object.
    """
    kind = serializers.CharField(max_length=256)
    kind_name = serializers.CharField(max_length=256)
    id = serializers.CharField(max_length=256)
    title = serializers.CharField(max_length=256)
    date_created = serializers.DateField()
    date_modified = serializers.DateField()
    hashes = serializers.DictField()
    extra = serializers.DictField()
    links = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_links(self, instance):
        """
        Translate the `links` property to a custom array of Hyperlink values.

        Parameters
        ----------
        instance : Target Obj instance

        Returns
        -------
        Hyperlink url for Target detail API endpoint
        """
        list_of_actions = action_checker(self.context.get('target_name'))
        # Build a list of endpoint_actions and compare with list_of_actions
        endpoint_actions = ['resource_download', 'resource_upload', 'resource_transfer_in']
        resource_actions = list_intersection(list_of_actions, endpoint_actions)

        links = link_builder(self, instance, resource_actions)

        return links

    def get_actions(self, instance):
        """
        Translate the `actions` property to a custom array of `action names`.

        Parameters
        ----------
        instance : Target Obj instance

        Returns
        -------
        Array of possible actions for the endpoint.
        """
        list_of_actions = action_checker(self.context.get('target_name'))
        action_list = []
        if 'resource_transfer_out' in list_of_actions:
            action_list.append('Transfer')

        return action_list
