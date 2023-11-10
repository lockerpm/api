from rest_framework import serializers

from locker_server.shared.constants.relay_address import RELAY_STATISTIC_TYPE_FORWARDED, \
    RELAY_STATISTIC_TYPE_BLOCKED_SPAM


class ReplySerializer(serializers.Serializer):
    lookup = serializers.CharField(max_length=255)
    encrypted_metadata = serializers.CharField()


class StatisticSerializer(serializers.Serializer):
    relay_address = serializers.CharField(max_length=128)
    type = serializers.ChoiceField(choices=[RELAY_STATISTIC_TYPE_FORWARDED, RELAY_STATISTIC_TYPE_BLOCKED_SPAM])
    amount = serializers.IntegerField(default=1)

    def to_internal_value(self, data):
        if "type" in data:
            data["type"] = data["type"].lower()
        return super(StatisticSerializer, self).to_internal_value(data)
