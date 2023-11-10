from rest_framework import serializers


class DetailSSOConfigurationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.sso_configuration_id,
            "identifier": instance.identifier,
            "enabled": instance.enabled,
            "sso_provider": instance.sso_provider.sso_provider_id,
            "sso_provider_options": instance.sso_provider_options,
            "creation_date": instance.creation_date,
            "revision_date": instance.revision_date
        }
        if instance.created_by:
            data.update({
                "created_by": {
                    "id": instance.created_by.user_id,
                    "username": instance.created_by.username
                }
            })
        return data


class RetrieveUserSerializer(serializers.Serializer):
    sso_identifier = serializers.CharField(max_length=255, required=False, allow_blank=True)
    code = serializers.CharField(required=True, allow_blank=False)
