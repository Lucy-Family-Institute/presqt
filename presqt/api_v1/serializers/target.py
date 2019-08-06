from django.urls import reverse
from rest_framework import serializers

class SupportedActions(serializers.Serializer):
    """
    Serializer for supported_actions objects inside the Target JSON.
    """
    resource_collection = serializers.BooleanField()
    resource_detail = serializers.BooleanField()
    resource_download = serializers.BooleanField()
    resource_upload = serializers.BooleanField()


class TargetsSerializer(serializers.Serializer):
    """
    Serializer for multiple Target objects.
    """
    name = serializers.CharField(max_length=256)
    supported_actions = SupportedActions()
    supported_hash_algorithms = serializers.StringRelatedField(many=True)
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
        links = []

        if instance['supported_actions']['resource_detail'] is True:
            reversed_detail = reverse('target', kwargs={'target_name': instance['name']})
            links.append({
                "name": 'detail',
                "link": self.context['request'].build_absolute_uri(reversed_detail),
                "method": "GET"})
        return links


class TargetSerializer(serializers.Serializer):
    """
    Serializer for a Target object.
    """
    name = serializers.CharField(max_length=256)
    supported_actions = SupportedActions()
    supported_hash_algorithms = serializers.StringRelatedField(many=True)
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
        links = []
        reversed_collection = reverse('resource_collection', kwargs={
            'target_name': instance['name']})
        if instance['supported_actions']['resource_collection'] is True:
            links.append({
                "name": "collection",
                "link": self.context['request'].build_absolute_uri(reversed_collection),
                "method": "GET"})
        
        return links
