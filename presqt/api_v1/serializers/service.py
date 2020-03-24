from django.urls import reverse
from rest_framework import serializers


class ServicesSerializer(serializers.Serializer):
    """
    Serializer for multiple Service objects.
    """
    name = serializers.CharField(max_length=256)
    readable_name = serializers.CharField(max_length=256)
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        """
        Translate the `links` property to a custom array of Hyperlink values.

        Parameters
        ----------
        instance : Service Obj instance

        Returns
        -------
        A list of hyperlink urls for Service detail API endpoint
        """
        reversed_service_detail = reverse(
            'service', kwargs={'service_name': instance['name']})

        return [{"name": 'Detail', "link": self.context['request'].build_absolute_uri(
            reversed_service_detail), "method": "GET"}]


class ServiceSerializer(serializers.Serializer):
    """
    Serializer for a Service object.
    """
    name = serializers.CharField(max_length=256)
    readable_name = serializers.CharField(max_length=256)
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        """
        Translate the `links` property to a custom array of Hyperlink values.

        Parameters
        ----------
        instance : Service Obj instance

        Returns
        -------
        A list of hyperlink urls for Service detail API endpoint
        """
        return [{"name": 'POST', "link": "PresQT-Service"}]
