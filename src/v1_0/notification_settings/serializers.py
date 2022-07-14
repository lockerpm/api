from rest_framework import serializers

from cystack_models.models.notifications.notification_settings import NotificationSetting


class ListNotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = ('notification', 'mail')

    def to_representation(self, instance):
        data = super(ListNotificationSettingSerializer, self).to_representation(instance)
        data["category"] = {
            "id": instance.category.id,
            "name": instance.category.name,
            "name_vi": instance.category.name_vi,
            "mail": instance.category.mail,
            "notification": instance.category.notification
        }
        return data
