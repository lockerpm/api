from rest_framework import serializers

from v1_0.ciphers.serializers import VaultItemSerializer
from v1_0.folders.serializers import FolderSerializer


class ImportFolderSerializer(serializers.Serializer):
    folders = FolderSerializer(many=True)

    def validate(self, data):
        folders = data.get("folders", [])
        if len(folders) > 1000:
            raise serializers.ValidationError(detail={"folders": ["You can only import up to 1000 folders at a time"]})
        return data


class ImportCipherSerializer(serializers.Serializer):
    ciphers = VaultItemSerializer(many=True)

    def validate(self, data):
        ciphers = data.get("ciphers", [])
        if len(ciphers) > 1000:
            raise serializers.ValidationError(detail={"ciphers": ["You can only import up to 1000 ciphers at a time"]})
        return data
