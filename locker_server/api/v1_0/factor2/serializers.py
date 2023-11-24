from rest_framework import serializers

from locker_server.shared.constants.factor2 import LIST_FA2_METHOD


class Factor2MailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, allow_blank=False)


class Factor2Serializer(serializers.Serializer):
    otp = serializers.CharField(required=True, max_length=16)
    method = serializers.ChoiceField(choices=LIST_FA2_METHOD)


class Factor2ActivateSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=64)
