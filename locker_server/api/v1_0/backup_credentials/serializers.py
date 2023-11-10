from rest_framework import serializers

from locker_server.core.entities.user.backup_credential import BackupCredential


class ListBackupCredentialSerializer(serializers.Serializer):
    def to_representation(self, instance: BackupCredential):
        data = {
            "id": instance.backup_credential_id,
            "master_password_hint": instance.master_password_hint,
            "creation_date": instance.creation_date,
            "key": instance.key,
            "keys": {
                "public_key": instance.public_key,
                "private_key": instance.private_key,
            },
            "fd_credential_id": instance.fd_credential_id,
            "fd_random": instance.fd_random,
        }
        return data


class DetailBackupCredentialSerializer(ListBackupCredentialSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class EncryptedPairKey(serializers.Serializer):
    encrypted_private_key = serializers.CharField()
    public_key = serializers.CharField()


class CreateBackupCredentialSerializer(serializers.Serializer):
    master_password_hash = serializers.CharField(allow_blank=False)
    master_password_hint = serializers.CharField(required=False, allow_blank=True, max_length=128)
    key = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    keys = EncryptedPairKey(many=False)
    fd_credential_id = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    fd_random = serializers.CharField(max_length=128, required=False, allow_blank=True, allow_null=True)
