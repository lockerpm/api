import re

from rest_framework import serializers

from locker_server.shared.constants.affiliate_submission import LIST_AFFILIATE_SUBMISSION_STATUS
from locker_server.shared.utils.app import now


class ListAffiliateSubmissionSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.affiliate_submission_id,
            "created_time": instance.created_time,
            "full_name": instance.full_name,
            "email": instance.domain.email,
            "phone": instance.domain.phone,
            "company": instance.company,
            "country": instance.country,
            "status": instance.status,
        }
        return data


class DetailAffiliateSubmissionSerializer(ListAffiliateSubmissionSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class CreateAffiliateSubmissionSerializer(serializers.Serializer):
    country = serializers.CharField(max_length=128, allow_null=True, default=None)
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField()
    company = serializers.CharField(max_length=128, required=False, allow_null=True, allow_blank=True, default="")
    status = serializers.ChoiceField(choices=LIST_AFFILIATE_SUBMISSION_STATUS)

    def validate(self, data):
        phone = data.get("phone")
        regex_phone = r'^[0-9]{6,25}$'
        if not re.match(regex_phone, phone):
            raise serializers.ValidationError(detail={"phone": ["The phone number is not valid"]})

        return data

    def to_internal_value(self, data):
        data["created_time"] = now()
        return super().to_internal_value(data)


class UpdateAffiliateSubmissionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=LIST_AFFILIATE_SUBMISSION_STATUS)
