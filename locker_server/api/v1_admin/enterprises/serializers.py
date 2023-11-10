from rest_framework import serializers


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
            "enterprise_name": instance.enterprise_name,
            "enterprise_address1": instance.enterprise_name,
            "enterprise_address2": instance.enterprise_name,
            "enterprise_phone": instance.enterprise_phone,
            "enterprise_country": instance.enterprise_country,
            "enterprise_postal_code": instance.enterprise_postal_code,
            "avatar": instance.avatar
        }
        return data


class DetailEnterpriseSerializer(ListEnterpriseSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class CreateEnterpriseSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_address1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_address2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_phone = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_country = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_postal_code = serializers.CharField(max_length=16, required=False, allow_blank=True)
    primary_admin = serializers.EmailField(required=False, allow_null=True, allow_blank=True, default="")
