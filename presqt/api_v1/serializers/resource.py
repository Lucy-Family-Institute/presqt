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
    detail = serializers.SerializerMethodField()

    def get_detail(self, instance):
        reversed_url = reverse(
            viewname='resource',
            kwargs={
                'target_name': self.context.get('target_name'),
                'resource_id': instance['id']})

        return self.context['request'].build_absolute_uri(reversed_url)


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
    download_url = serializers.SerializerMethodField()

    def get_download_url(self, instance):
        reversed_url = reverse(
            viewname='resource',
            kwargs={
                'target_name': self.context.get('target_name'),
                'resource_id': instance['id'],
                'resource_format': 'zip'})

        return self.context['request'].build_absolute_uri(reversed_url)
