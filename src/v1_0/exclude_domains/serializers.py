import urllib.parse
from urllib.parse import urlparse

from rest_framework import serializers

from cystack_models.models.users.exclude_domains import ExcludeDomain
from shared.utils.network import is_valid_domain, is_valid_ip, extract_root_domain


class ExcludeDomainSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(max_length=255)

    class Meta:
        model = ExcludeDomain
        fields = ('id', 'created_time', 'domain')
        read_only_fields = ('id', 'created_time', )

    def validate(self, data):
        domain = data.get("domain")
        url = urllib.parse.unquote(domain)
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = f"https://{url}"
            parsed_url = urlparse(url)
        domain = parsed_url.netloc
        is_domain = is_valid_domain(domain)
        is_ip = is_valid_ip(domain)
        if (is_domain is False) and (is_ip is False):
            raise serializers.ValidationError(detail={'domain': [
                'This domain or ip is invalid', 'Domain hoặc ip không hợp lệ'
            ]})
        if is_domain:
            data["domain"] = extract_root_domain(domain=domain)
        return data

    def to_representation(self, instance):
        return super().to_representation(instance)

