from rest_framework import serializers


class ListNotificationSettingSerializer(serializers.Serializer):

    def to_representation(self, instance):
        data = {
            "notification": instance.notification,
            "mail": instance.mail
        }
        if instance.category:
            category = instance.category
            data.update({
                "category": {
                    "id": category.notification_category_id,
                    "name": category.name,
                    "name_vi": category.name_vi,
                    "mail": category.mail,
                    "notification": category.notification
                }
            })
        return data


class DetailNotificationSerializer(ListNotificationSettingSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class NotificationAllSerializer(serializers.Serializer):
    notification = serializers.BooleanField()


class UpdateNotificationSettingSerializer(serializers.Serializer):
    notification = serializers.BooleanField(required=False)
    mail = serializers.BooleanField(required=False)
