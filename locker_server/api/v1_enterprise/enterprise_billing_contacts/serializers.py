from rest_framework import serializers


class ListEnterpriseBillingContactSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.enterprise_billing_contact_id,
            "created_time": instance.created_time,
            "email": instance.email,
        }
        return data


class DetailEnterpriseBillingContactSerializer(serializers.ListSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class CreateEnterpriseBillingContactSerializer(serializers.Serializer):
    email = serializers.EmailField()
