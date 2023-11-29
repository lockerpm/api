import json

from rest_framework import serializers

from locker_server.core.entities.user.backup_credential import BackupCredential


class ListBackupCredentialSerializer(serializers.Serializer):
    def to_representation(self, instance: BackupCredential):
        data = {
            "id": instance.backup_credential_id,
            "master_password_hint": instance.master_password_hint,
            "creation_date": instance.creation_date,
            "key": instance.key,
            "security_keys": instance.security_keys,
            "fd_credential_id": instance.fd_credential_id,
            "fd_random": instance.fd_random,
        }
        return data


class DetailBackupCredentialSerializer(ListBackupCredentialSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class SecurityKey(serializers.Serializer):
    name = serializers.CharField(required=True)
    creation_date = serializers.FloatField(required=False)
    last_use_date = serializers.FloatField(required=False)


class CreateBackupCredentialSerializer(serializers.Serializer):
    master_password_hash = serializers.CharField(allow_blank=False)
    master_password_hint = serializers.CharField(required=False, allow_blank=True, max_length=128)
    key = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    security_keys = SecurityKey(required=False, many=True)
    fd_credential_id = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    fd_random = serializers.CharField(max_length=128, required=False, allow_blank=True, allow_null=True)

    def to_internal_value(self, data):
        security_keys = data.get("security_keys")
        if security_keys:
            security_keys_str = json.dumps(security_keys)
            data.update({
                "security_keys": security_keys_str
            })
        return data
