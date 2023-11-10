import urllib.parse
from urllib.parse import urlparse

from rest_framework import serializers

from locker_server.shared.utils.network import is_valid_ip, extract_root_domain, is_valid_domain


class ExcludeDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255)

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
        data = {
            "id": instance.exclude_domain_id,
            "domain": instance.domain,
            "created_time": instance.created_time
        }
        return data
