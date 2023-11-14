from rest_framework import serializers

from locker_server.shared.constants.ciphers import KDF_TYPE
from locker_server.shared.constants.enterprise_members import ENTERPRISE_LIST_ROLE, E_MEMBER_ROLE_MEMBER


class ListEnterpriseSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.enterprise_id,
            "organization_id": instance.enterprise_id,
            "name": instance.name,
            "description": instance.description,
            "creation_date": instance.creation_date,
            "revision_date": instance.revision_date,
            "locked": instance.locked,
            "avatar": instance.avatar,
        }
        return data


class DetailEnterpriseSerializer(ListEnterpriseSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update({
            "enterprise_name": instance.enterprise_name,
            "enterprise_address1": instance.enterprise_name,
            "enterprise_address2": instance.enterprise_name,
            "enterprise_phone": instance.enterprise_phone,
            "enterprise_country": instance.enterprise_country,
            "enterprise_postal_code": instance.enterprise_postal_code,
        })
        return data


class UpdateEnterpriseSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_address1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_address2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_phone = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_country = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_postal_code = serializers.CharField(max_length=16, required=False, allow_blank=True)


class EncryptedPairKey(serializers.Serializer):
    encrypted_private_key = serializers.CharField()
    public_key = serializers.CharField()


class CreateMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ENTERPRISE_LIST_ROLE, default=E_MEMBER_ROLE_MEMBER)
    master_password_hash = serializers.CharField(allow_blank=False)
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    kdf = serializers.IntegerField(default=0)
    kdf_iterations = serializers.IntegerField(default=100000)
    key = serializers.CharField()
    keys = EncryptedPairKey(many=False)
    master_password_hint = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate(self, data):
        kdf_type = data.get("kdf_type", 0)
        if not KDF_TYPE.get(kdf_type):
            raise serializers.ValidationError(detail={"kdf": ["This KDF Type is not valid"]})
        kdf_iterations = data.get("kdf_iterations", 100000)
        if kdf_iterations < 5000 or kdf_iterations > 1000000:
            raise serializers.ValidationError(detail={
                "kdf_iterations": ["KDF iterations must be between 5000 and 1000000"]
            })

        return data


class CreateMultipleMemberSerializer(serializers.Serializer):
    members = serializers.ListSerializer(
        child=CreateMemberSerializer()
    )
