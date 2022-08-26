from rest_framework import serializers

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
            "metadata": instance.get_metadata(),
        }
        return data
