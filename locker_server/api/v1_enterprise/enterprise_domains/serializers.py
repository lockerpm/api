from rest_framework import serializers

from locker_server.shared.utils.network import is_valid_domain, extract_root_domain


class ListDomainSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.domain_id,
            "created_time": instance.created_time,
            "updated_time": instance.updated_time,
            "domain": instance.domain,
            "verification": instance.verification,
            "auto_approve": instance.auto_approve,
        }
        return data


class DetailDomainSerializer(ListDomainSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


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


class UpdateDomainSerializer(serializers.Serializer):
    auto_approve = serializers.BooleanField()
