from rest_framework import serializers

from shared.constants.event import LOG_TYPES
from cystack_models.models.events.events import Event


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'type', 'creation_date', )
        read_only_fields = ('id', 'type', 'creation_date', )

    def to_representation(self, instance):
        data = {
            "id": instance.id,
            "type": instance.type,
            "creation_date": instance.creation_date,
            "acting_user": {
                "id": instance.acting_user_id,
            },
            "user": {
                "id": instance.user_id,
            },
            "ip_address": instance.ip_address,
            "cipher_id": instance.cipher_id,
            "collection_id": instance.collection_id,
            "device_type": instance.device_type,
            "group_id": instance.group_id,
            "enterprise_id": instance.team_id,
            "enterprise_member_id": instance.team_member_id,
            "description": self.__get_description(instance),
        }
        return data

    @staticmethod
    def __get_description(log):
        log_type = int(log.type)
        description = LOG_TYPES.get(log_type, {"vi": "", "en": ""})

        if 1100 <= log_type <= 1116:
            description["vi"] = description["vi"].format(log.cipher_id)
            description["en"] = description["en"].format(log.cipher_id)
        elif 1300 <= log_type <= 1302:
            description["vi"] = description["vi"].format(log.collection_id)
            description["en"] = description["en"].format(log.collection_id)
        elif 1400 <= log_type <= 1402:
            description["vi"] = description["vi"].format(log.group_id)
            description["en"] = description["en"].format(log.group_id)

        elif 1500 <= log_type <= 1504:
            description["vi"] = description["vi"].format(log.team_member_id)
            description["en"] = description["en"].format(log.team_member_id)

        elif log_type >= 1800:
            description["vi"] = description["vi"].format(log.get_metadata())
            description["en"] = description["en"].format(log.get_metadata())

        return description
