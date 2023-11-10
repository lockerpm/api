from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.micro_service_permissions.user_permission import UserPermission
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.constants.device_type import CLIENT_ID_MOBILE
from locker_server.shared.utils.app import now


class UserViewSet(APIBaseViewSet):
    permission_classes = (UserPermission, )
    lookup_value_regex = r'[0-9]+'
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        return super(UserViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            user_id = int(self.kwargs.get("pk"))
            user = self.user_service.retrieve_or_create_by_id(user_id=user_id)
            return user
        except ValueError:
            raise NotFound

    def retrieve(self, request, *args, **kwargs):
        try:
            user_id = int(self.kwargs.get("pk"))
            user = self.user_service.retrieve_by_id(user_id=user_id)
            return Response(status=status.HTTP_200_OK, data={"id": user.user_id})
        except (ValueError, UserDoesNotExistException):
            raise NotFound

    @action(methods=["post"], detail=True)
    def first_login(self, request, *args, **kwargs):
        user = self.get_object()
        first_login = self.request.data.get("first_login", now())
        if not user.first_login:
            self.user_service.update_user(user_id=user.user_id, user_update_data={
                "first_login": first_login
            })
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def search_by_device(self, request, *args, **kwargs):
        device_identifier = request.data.get("device_identifier")
        devices = self.device_service.list_devices(**{
            "device_identifier": device_identifier
        })
        users = [{
            "id": device.user.user_id,
            "activated": device.user.activated
        } for device in devices]
        return Response(status=status.HTTP_200_OK, data=users)

    @action(methods=["post"], detail=False)
    def search_by_user(self, request, *args, **kwargs):
        try:
            user = self.user_service.retrieve_by_id(user_id=request.data.get("user_id"))
            mobile_devices = self.device_service.list_devices(**{
                "user_id": user.user_id, "client_id": CLIENT_ID_MOBILE
            })
            return Response(status=200, data={
                "id": user.user_id,
                "activated": user.activated,
                "use_mobile": True if mobile_devices else False,
                "last_login": user.last_request_login
            })
        except UserDoesNotExistException:
            raise NotFound
