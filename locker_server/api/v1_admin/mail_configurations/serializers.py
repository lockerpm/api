from rest_framework import serializers

from locker_server.shared.constants.mail_provider import *


class MailConfigurationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "mail_provider": instance.mail_provider.mail_provider_id,
            "mail_provider_options": instance.mail_provider_options,
            "sending_domain": instance.sending_domain,
            "from_email": instance.from_email,
            "from_name": instance.from_name
        }
        return data


class SMTPOptionSerializer(serializers.Serializer):
    smtp_host = serializers.CharField(max_length=255)
    smtp_port = serializers.CharField(max_length=255)
    smtp_username = serializers.CharField(max_length=255)
    smtp_password = serializers.CharField(max_length=255)

    def validate(self, data):
        port = data.get("smtp_port")
        try:
            int(port)
        except ValueError:
            raise serializers.ValidationError(detail={"smtp_port": ["The SMTP Port is not valid"]})
        return data


class SendgridOptionSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=512)


class UpdateMailConfigurationSerializer(serializers.Serializer):
    mail_provider = serializers.ChoiceField(choices=LIST_VALID_MAIL_PROVIDERS)
    sending_domain = serializers.CharField(max_length=255, allow_blank=True, allow_null=True, required=False)
    from_email = serializers.EmailField(max_length=255, allow_blank=True, allow_null=True)
    from_name = serializers.CharField(max_length=255, allow_blank=True, allow_null=True, required=False)
    mail_provider_options = serializers.DictField(required=False, allow_null=True)

    def validate(self, data):
        mail_provider = data.get("mail_provider")
        mail_provider_options = data.get("mail_provider_options")
        if mail_provider == MAIL_PROVIDER_SENDGRID:
            option_srl = SendgridOptionSerializer(data=mail_provider_options)
        else:
            option_srl = SMTPOptionSerializer(data=mail_provider_options)
        option_is_valid = option_srl.is_valid(raise_exception=False)
        if option_is_valid is False:
            # option_srl.errors
            raise serializers.ValidationError(detail={"mail_provider_options": option_srl.errors})
        data["mail_provider_options"] = option_srl.validated_data
        return data


class SendTestMailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, required=False, allow_null=True, allow_blank=True)
