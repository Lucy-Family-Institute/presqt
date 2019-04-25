from django.urls import reverse
from rest_framework import serializers


class TargetsSerializer(serializers.Serializer):
    """
    Serializer multiple Target objects.
    """
    name = serializers.CharField(max_length=256)
    read = serializers.BooleanField()
    write = serializers.BooleanField()
    detail = serializers.SerializerMethodField()

    def get_detail(self, instance):
        """
        Translate the `detail` property to a custom Hyperlink value.

        Parameters
        ----------
        instance : Target Obj instance

        Returns
        -------
        Hyperlink url for Target detail API endpoint
        """
        reversed_url = reverse('target', kwargs={'target_name': instance['name']})
        hyperlink = self.context['request'].build_absolute_uri(reversed_url)
        return hyperlink


class TargetSerializer(serializers.Serializer):
    """
    Serializer for a Target object.
    """
    name = serializers.CharField(max_length=256)
    read = serializers.BooleanField()
    write = serializers.BooleanField()