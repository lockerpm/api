from rest_framework import serializers


class ReplySerializer(serializers.Serializer):
    lookup = serializers.CharField(max_length=255)
    encrypted_metadata = serializers.CharField()
