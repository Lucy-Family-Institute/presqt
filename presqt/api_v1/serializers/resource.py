from rest_framework import serializers

class ResourcesSerializer(serializers.Serializer):
    """
    Serializer for a given Resource object.
    """
    kind = serializers.CharField(max_length=256)
    kind_name = serializers.CharField(max_length=256)
    id = serializers.CharField(max_length=256)
    container = serializers.CharField(max_length=256)