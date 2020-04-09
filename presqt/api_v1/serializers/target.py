from django.urls import reverse
from rest_framework import serializers

from presqt.api_v1.utilities import action_checker, link_builder
from presqt.utilities import list_intersection


class SupportedActions(serializers.Serializer):
    """
    Serializer for supported_actions objects inside the Target JSON.
    """
    resource_collection = serializers.BooleanField()
    resource_detail = serializers.BooleanField()
    resource_download = serializers.BooleanField()
    resource_upload = serializers.BooleanField()
    resource_transfer_in = serializers.BooleanField()
    resource_transfer_out = serializers.BooleanField()


class SupportedTransferPartners(serializers.Serializer):
    """
    Serializer for supported_transfer_partners objects inside the Target JSON.
    """
    transfer_in = serializers.ListField(child=serializers.CharField())
    transfer_out = serializers.ListField(child=serializers.CharField())


class TargetsSerializer(serializers.Serializer):
    """
    Serializer for multiple Target objects.
    """
    name = serializers.CharField(max_length=256)
    readable_name = serializers.CharField(max_length=256)
    supported_actions = SupportedActions()
    supported_transfer_partners = SupportedTransferPartners()
    supported_hash_algorithms = serializers.StringRelatedField(many=True)
    infinite_depth = serializers.BooleanField()
    search_parameters = serializers.ListField()
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        """
        Translate the `links` property to a custom array of Hyperlink values.

        Parameters
        ----------
        instance : Target Obj instance

        Returns
        -------
        A list of hyperlink urls for Target detail API endpoint
        """
        reversed_target_detail = reverse(
            'target', kwargs={'target_name': instance['name']})

        return [{"name": 'Detail', "link": self.context['request'].build_absolute_uri(
            reversed_target_detail), "method": "GET"}]


class TargetSerializer(serializers.Serializer):
    """
    Serializer for a Target object.
    """
    name = serializers.CharField(max_length=256)
    readable_name = serializers.CharField(max_length=256)
    supported_actions = SupportedActions()
    supported_transfer_partners = SupportedTransferPartners()
    supported_hash_algorithms = serializers.StringRelatedField(many=True)
    infinite_depth = serializers.BooleanField()
    search_parameters = serializers.ListField()
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        """
        Translate the `links` property to a custom array of Hyperlink values.

        Parameters
        ----------
        instance : Target Obj instance

        Returns
        -------
        A list of hyperlink urls for Target detail API endpoint
        """
        list_of_actions = action_checker(instance['name'])
        # Build a list of endpoint_actions to compare with list of actions
        endpoint_actions = ['resource_collection', 'resource_upload', 'resource_transfer_in']
        resources_actions = list_intersection(list_of_actions, endpoint_actions)

        links = link_builder(self, instance, resources_actions)

        return links
