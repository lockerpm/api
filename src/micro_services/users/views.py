from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

from micro_services.apps import MicroServiceViewSet
from shared.permissions.micro_service_permissions.user_permissions import UserPermission
from shared.utils.app import now


class UserViewSet(MicroServiceViewSet):
    permission_classes = (UserPermission, )
    lookup_value_regex = r'[0-9]+'
    http_method_names = ["head", "options", "post", "put"]

    def get_serializer_class(self):
        return super(UserViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            user_id = int(self.kwargs.get("pk"))
            user = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
            return user
        except ValueError:
            raise NotFound

    @action(methods=["post"], detail=True)
    def first_login(self, request, *args, **kwargs):
        user = self.get_object()
        first_login = self.request.data.get("first_login", now())
        if not user.first_login:
            user.first_login = first_login
            user.save()
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def search_by_device(self, request, *args, **kwargs):
        device_identifier = request.data.get("device_identifier")
        from cystack_models.models import Device
        devices = Device.objects.filter(device_identifier=device_identifier).select_related('user')
        users = [{
            "id": device.user.user_id,
            "activated": device.user.activated
        } for device in devices]
        return Response(status=200, data=users)

    @action(methods=["post"], detail=False)
    def search_by_user(self, request, *args, **kwargs):
        from cystack_models.models import User
        try:
            user = User.objects.get(user_id=request.data.get("user_id"))
            return Response(status=200, data={
                "id": user.user_id,
                "activated": user.activated,
                "use_mobile": user.user_devices.filter(client_id="mobile").exists(),
                "last_login": user.last_request_login
            })
        except User.DoesNotExist:
            raise NotFound
