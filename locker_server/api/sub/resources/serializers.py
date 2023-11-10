from rest_framework import serializers


class CountrySerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "country_code": instance.country_code,
            "country_name": instance.country_name,
            "country_phone_code": instance.country_phone_code,
        }
        return data
