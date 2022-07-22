from rest_framework import serializers

from cystack_models.models.enterprises.domains.domains import Domain
from shared.utils.network import is_valid_domain, extract_root_domain


class ListDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'created_time', 'updated_time', 'domain', 'verification')


class CreateDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(required=True, max_length=128)
    description = serializers.CharField(allow_blank=True, default="")

    def validate(self, data):
        domain = data.get("domain")
        if not is_valid_domain(domain) or domain == "localhost":
            raise serializers.ValidationError(detail={"domain": ["This domain is not valid", "Domain không hợp lệ"]})

        root_domain = extract_root_domain(domain=domain)
        data["root_domain"] = root_domain
        return data
