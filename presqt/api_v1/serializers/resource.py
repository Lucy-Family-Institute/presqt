from rest_framework import serializers

class ResourcesSerializer(serializers.Serializer):
    """
    Serializer for a given resource object in a target resource list.
    """
    kind = serializers.CharField(max_length=256)
    kind_name = serializers.CharField(max_length=256)
    id = serializers.CharField(max_length=256)
    container = serializers.CharField(max_length=256)
    title = serializers.CharField(max_length=256)


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

    # extra
    # links eventually
    # hashes