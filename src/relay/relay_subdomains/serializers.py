from django.db.models import Sum
from rest_framework import serializers

from cystack_models.models.relay.relay_subdomains import RelaySubdomain


class SubdomainSerializer(serializers.Serializer):
    def to_representation(self, instance):
        relay_addresses = instance.relay_addresses.all()
        num_spam = relay_addresses.aggregate(Sum('num_spam')).get("num_spam__sum") or 0
        num_forwarded = relay_addresses.aggregate(Sum('num_forwarded')).get("num_forwarded__sum") or 0
        return {
            "id": instance.id,
            "subdomain": instance.subdomain,
            "created_time": instance.created_time,
            "num_alias": relay_addresses.count(),
            "num_spam": num_spam,
            "num_forwarded": num_forwarded,
        }


class UpdateSubdomainSerializer(serializers.Serializer):
    subdomain = serializers.CharField(max_length=64, min_length=3)

    def validate(self, data):
        subdomain = data.get("subdomain")

        if RelaySubdomain.valid_subdomain(subdomain=subdomain) is False:
            raise serializers.ValidationError(detail={"subdomain": [
                "This subdomain is not valid (has black words, blocked words, etc...)",
                "Tên miền phụ này có chứa từ khóa không hợp lệ"
            ]})

        return data


class UseRelaySubdomainSerializer(serializers.Serializer):
    use_relay_subdomain = serializers.BooleanField()
