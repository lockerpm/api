from rest_framework import serializers


class ListRelayAddressSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.relay_address_id,
            "address": instance.address,
            "subdomain": instance.subdomain.subdomain if instance.subdomain else None,
            "domain": instance.domain.relay_domain_id,
            "enabled": instance.enabled,
            "block_spam": instance.block_spam,
            "description": instance.description,
            "created_time": instance.created_time,
            "updated_time": instance.updated_time,
            "num_forwarded": instance.num_forwarded,
            "num_blocked": instance.num_blocked,
            "num_replied": instance.num_replied,
            "num_spam": instance.num_spam,
            "full_address": instance.full_address,
        }
        return data


class DetailRelayAddressSerializer(ListRelayAddressSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class CreateRelayAddressSerializer(serializers.Serializer):
    """"""


class UpdateRelayAddressSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=64, min_length=6)
    description = serializers.CharField(allow_blank=True, required=False)
    enabled = serializers.BooleanField(required=False)
    block_spam = serializers.BooleanField(required=False)
