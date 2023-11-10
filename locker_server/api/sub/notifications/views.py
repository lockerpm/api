from django.conf import settings
from rest_framework.decorators import action
from rest_framework import pagination, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.core.exceptions.notification_exception import NotificationDoesNotExistException
from .serializers import *
from locker_server.api.permissions.locker_permissions.notification_pwd_permission import NotificationPwdPermission


class NotificationViewSet(APIBaseViewSet):
    http_method_names = ["head", "options", "get", "post", "put"]
    permission_classes = (NotificationPwdPermission,)

    def get_client_agent(self):
        return self.request.META.get("HTTP_USER_AGENT") or ''

    def get_serializer_class(self):
        if self.action == "update":
            self.serializer_class = UpdateNotificationSerializer
        elif self.action == "list":
            self.serializer_class = ListNotificationSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailNotificationSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        current_user = self.request.user
        notifications = self.notification_service.list_notifications(**{
            "user_id": current_user.user_id,
            "read": self.request.query_params.get('read', None),
            "scope": self.request.query_params.get('scope', "app")
        })
        return notifications

    def get_object(self):
        user = self.request.user
        try:
            notification = self.notification_service.get_notification_by_id(notification_id=self.kwargs.get("id"))
            if notification.user.user_id != user.user_id:
                raise NotFound
        except NotificationDoesNotExistException:
            raise NotFound

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 20))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 20
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data.update({
                "unread_count": self.notification_service.count_notifications(**{
                    "user_id": user.user_id,
                    "read": "0",
                    "scope": self.request.query_params.get('scope', settings.SCOPE_PWD_MANAGER)
                })
            })
            return response
        serializer = self.get_serializer(queryset, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        current_user = self.request.user
        notification_id = kwargs.get("id")

        if notification_id == "read_all":
            return self.read_all(request, *args, **kwargs)

        notification = self.get_object()
        data = notification.to_json()
        return Response(status=status.HTTP_200_OK, data=data)

    def update(self, request, *args, **kwargs):
        current_user = self.request.user
        notification_id = kwargs.get("id")

        if notification_id == "read_all":
            return self.read_all(request, *args, **kwargs)

        notification = self.get_object()

        self.serializer_class = UpdateNotificationSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        read = serializer.validated_data.get("read")
        metadata = request.data.get("metadata") or {}
        clicked = metadata.get("clicked")
        try:
            updated_notification = self.notification_service.update_notification(
                notification_id=notification.notification_id,
                read=read,
                clicked=clicked
            )
        except NotificationDoesNotExistException:
            raise NotFound

        data = updated_notification.to_json()
        return Response(status=status.HTTP_200_OK, data=data)

    @action(methods=["get"], detail=False)
    def read_all(self, request, *args, **kwargs):
        current_user = self.request.user
        self.notification_service.read_all(**{
            "user_id": current_user.user_id,
            "read": "0",
            "scope": self.request.query_params.get('scope', "app")
        })

        return Response(status=status.HTTP_200_OK)
