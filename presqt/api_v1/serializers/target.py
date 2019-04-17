from django.urls import reverse
from rest_framework import serializers


class TargetsSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256)
    read = serializers.BooleanField()
    write = serializers.BooleanField()
    detail = serializers.SerializerMethodField()

    def get_detail(self, instance):
        reversed_url = reverse('target_detail', kwargs={'target_name': instance['name']})
        hyper = self.context['request'].build_absolute_uri(reversed_url)
        return hyper


class TargetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256)
    read = serializers.BooleanField()
    write = serializers.BooleanField()