import json

from rest_framework import serializers
from django.urls import reverse


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
        links = []

        resource_detail, resource_download, resource_upload = target_checker(
            self.context.get('target_name'))

        if resource_detail is True:
            reversed_detail = reverse(
                viewname='resource',
                kwargs={'target_name': self.context.get('target_name'),
                        'resource_id': instance['id']})
            links.append({
                "name": "Detail",
                "link": self.context['request'].build_absolute_uri(reversed_detail),
                "method": "GET"})

        if resource_download is True:
            reversed_download = reverse(
                viewname='resource',
                kwargs={'target_name': self.context.get('target_name'),
                        'resource_id': instance['id'], 'resource_format': 'zip'})
            links.append({
                "name": "Download",
                "link": self.context['request'].build_absolute_uri(reversed_download),
                "method": "GET"})

        if resource_upload is True:
            if instance['kind'] == 'container':
                links.append({
                    "name": "Upload",
                    "link": self.context['request'].build_absolute_uri(reversed_detail),
                    "method": "POST"})
            else:
                pass

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
    size = serializers.IntegerField()
    hashes = serializers.DictField()
    extra = serializers.DictField()
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

        resource_detail, resource_download, resource_upload = target_checker(
            self.context.get('target_name'))

        if resource_download is True:
            reverse_download = reverse(
                viewname='resource',
                kwargs={
                    'target_name': self.context.get('target_name'),
                    'resource_id': instance['id'],
                    'resource_format': 'zip'})
            links.append({
                "name": "Download",
                "link": self.context['request'].build_absolute_uri(reverse_download),
                "method": "GET"})

        if resource_upload is True:
            if instance['kind'] == 'container':
                reversed_upload = reverse(
                    viewname='resource',
                    kwargs={'target_name': self.context.get('target_name'),
                            'resource_id': instance['id']})
                links.append({
                    "name": "Upload",
                    "link": self.context['request'].build_absolute_uri(reversed_upload),
                    "method": "POST"})

        return links


def target_checker(target_name):
    """
    Checks in on targets.json and determines what actions are available for the requesting target.

    Parameters
    ----------
    target_name: str

    Returns
    -------
    """
    with open('presqt/targets.json') as target_data:
        target_json = json.load(target_data)
        for target in target_json:
            if target['name'] == target_name:
                resource_detail = target['supported_actions']['resource_detail']
                resource_download = target['supported_actions']['resource_download']
                resource_upload = target['supported_actions']['resource_upload']
            else:
                pass

    return resource_detail, resource_download, resource_upload
