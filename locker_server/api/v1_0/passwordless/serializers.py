from rest_framework import serializers


class PasswordlessCredentialSerializer(serializers.Serializer):
    credential_id = serializers.CharField(max_length=255)
