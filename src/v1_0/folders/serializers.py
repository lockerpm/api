from rest_framework import serializers


class FolderSerializer(serializers.Serializer):
    name = serializers.CharField()
