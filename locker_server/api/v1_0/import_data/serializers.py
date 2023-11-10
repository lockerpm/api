from rest_framework import serializers

from locker_server.api.v1_0.ciphers.serializers import VaultItemSerializer
from locker_server.api.v1_0.folders.serializers import FolderSerializer
from locker_server.shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD


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
        imported_ciphers = [cipher for cipher in ciphers if cipher.get("type") != CIPHER_TYPE_MASTER_PASSWORD]
        data["ciphers"] = imported_ciphers
        return data
