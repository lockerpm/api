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

