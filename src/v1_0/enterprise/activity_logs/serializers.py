from rest_framework import serializers

from cystack_models.models.events.events import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'type', 'creation_date', )
        read_only_fields = ('id', 'type', 'creation_date', )

    def to_representation(self, instance):
        data = {
            "id": instance.id,
            "type": instance.type,
            "creation_date": instance.creation_date
        }
        return data