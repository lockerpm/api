from rest_framework import serializers


class ListNotificationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return instance.to_json()


class DetailNotificationSerializer(ListNotificationSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class UpdateNotificationSerializer(serializers.Serializer):
    read = serializers.BooleanField(required=True)
