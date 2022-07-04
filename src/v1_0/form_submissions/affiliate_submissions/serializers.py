import re

from rest_framework import serializers

from cystack_models.models import Country
from cystack_models.models.form_submissions.affiliate_submissions import AffiliateSubmission


class AffiliateSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateSubmission
        read_only_fields = ('id', )

    def validate(self, data):
        country = data.get("country")
        if country and Country.objects.filter(country_name=country).exists() is False:
            raise serializers.ValidationError(detail={"country": ["The country does not exist"]})

        phone = data.get("phone")
        regex_phone = r'^[0-9]{6,25}$'
        if not re.match(regex_phone, phone):
            raise serializers.ValidationError(detail={"phone": ["The phone number is not valid"]})

        return data
