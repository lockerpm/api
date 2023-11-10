from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.notification_setting_pwd_permission import \
    NotificationSettingPwdPermission
from locker_server.core.exceptions.notification_setting_exception import NotificationSettingDoesNotExistException
from .serializers import *


class NotificationSettingPwdViewSet(APIBaseViewSet):
    permission_classes = (NotificationSettingPwdPermission,)
    http_method_names = ["head", "options", "get", "put"]
    lookup_value_regex = r'[a-z_]+'

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListNotificationSettingSerializer
        elif self.action == "update":
            self.serializer_class = UpdateNotificationSettingSerializer
        return super().get_serializer_class()

    def get_notification_setting(self, user):
        try:
            category_id = self.kwargs.get("category_id")
            notification_setting = self.notification_setting_service.get_notification_setting_by_category_id(
                user_id=user.user_id,
                category_id=category_id
            )
            return notification_setting
        except NotificationSettingDoesNotExistException:
            raise NotFound

    def get_queryset(self):
        user = self.request.user
        query_params = self.request.query_params
        notification_settings = self.notification_setting_service.list_user_notification_settings(
            user_id=user.user_id,
            **{
                "type": query_params.get("type"),
            }
        )
        return notification_settings

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "0")
        size_param = self.request.query_params.get("size", 10)
        page_size_param = self.check_int_param(size_param)
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param or 10
        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        notification_setting = self.get_notification_setting(user=user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            updated_notification_setting = self.notification_setting_service.update_notification_setting(
                notification_setting_id=notification_setting.notification_setting_id,
                notification_update_data=validated_data
            )
        except NotificationSettingDoesNotExistException:
            raise NotFound

        return Response(status=status.HTTP_200_OK, data={"success": True})
