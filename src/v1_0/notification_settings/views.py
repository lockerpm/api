from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.decorators import action

from cystack_models.models import User
from shared.permissions.locker_permissions.notification_setting_pwd_permission import NotificationSettingPermission
from v1_0.apps import PasswordManagerViewSet
from v1_0.notification_settings.serializers import ListNotificationSettingSerializer


class NotificationSettingPwdViewSet(PasswordManagerViewSet):
    permission_classes = (NotificationSettingPermission, )
    http_method_names = ["head", "options", "get", "put"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListNotificationSettingSerializer
        return super(NotificationSettingPwdViewSet, self).get_serializer_class()

    def get_notification_setting(self, user: User):
        try:
            notification_setting = user.notification_settings.get(category_id=self.kwargs.get("category_id"))
            return notification_setting
        except ObjectDoesNotExist:
            raise NotFound

    def list(self, request, *args, **kwargs):
        user = self.request.user
        if user.notification_settings.all().exists() is False:
            user.notification_settings.model.create_default_multiple(user)
        notification_settings = user.notification_settings.all().order_by('category_id')
        type_param = self.request.query_params.get("type")
        if type_param == "notification":
            notification_settings = notification_settings.filter(category__notification=True)
        elif type_param == "mail":
            notification_settings = notification_settings.filter(category__mail=True)

        serializer = self.get_serializer(notification_settings, many=True)
        return Response(status=200, data=serializer.data)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        notification_setting = self.get_notification_setting(user=user)
        toggle_notification = request.data.get("notification")
        toggle_mail = request.data.get("mail")

        if toggle_notification is not None:
            notification_setting.on_off_notification(turn_on=toggle_notification)
        if toggle_mail is not None:
            notification_setting.on_off_mail(turn_on=toggle_mail)
        return Response(status=200, data={"success": True})
