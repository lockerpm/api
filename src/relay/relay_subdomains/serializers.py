from rest_framework import serializers

from cystack_models.models.relay.relay_subdomains import RelaySubdomain


class SubdomainSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {
            "id": instance.id,
            "subdomain": instance.subdomain
        }


class UpdateSubdomainSerializer(serializers.Serializer):
    subdomain = serializers.CharField(max_length=128, min_length=3)

    def validate(self, data):
        subdomain = data.get("subdomain")

        if RelaySubdomain.valid_subdomain(subdomain=subdomain) is False:
            raise serializers.ValidationError(detail={"subdomain": [
                "This relay subdomain is not valid (has black words, blocked words, etc...)"
            ]})

        return data


class UseRelaySubdomainSerializer(serializers.Serializer):
    use_relay_subdomain = serializers.BooleanField()
