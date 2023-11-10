from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from locker_server.api.permissions.locker_permissions.user_sub_permission import UserSubPermission
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.api.api_base_view import APIBaseViewSet
from .serializer import UserMeSerializer, UpdateMeSerializer


class UserViewSet(APIBaseViewSet):
    http_method_names = ["head", "options", "get", "post", "put"]
    permission_classes = (UserSubPermission, )

    def get_serializer_class(self):
        if self.action == "retrieve":
            self.serializer_class = UserMeSerializer
        elif self.action == "update":
            self.serializer_class = UpdateMeSerializer
        return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(user, many=False)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            updated_user = self.user_service.update_user(
                user_id=user.user_id,
                user_update_data={
                    "language": validated_data.get("language"),
                    "full_name": validated_data.get("full_name")
                }
            )
        except UserDoesNotExistException:
            raise NotFound

        return Response(status=status.HTTP_200_OK, data=UserMeSerializer(updated_user, many=False).data)

    @action(methods=["post"], detail=False)
    def logout(self, request, **data):
        current_user = self.request.user
        device_access_token = request.auth
        self.user_service.revoke_all_sessions(
            user=current_user,
            exclude_sso_token_ids=[device_access_token.sso_token_id]
        )
        return Response(status=status.HTTP_200_OK)
