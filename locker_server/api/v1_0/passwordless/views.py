import random

from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.passwordless_pwd_permission import PasswordlessPwdPermission
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from .serializers import PasswordlessCredentialSerializer


class PasswordlessPwdViewSet(APIBaseViewSet):
    permission_classes = (PasswordlessPwdPermission,)
    http_method_names = ["head", "options", "get", "post", ]

    def get_serializer_class(self):
        if self.action == "credential":
            self.serializer_class = PasswordlessCredentialSerializer
        return super().get_serializer_class()

    @action(methods=["get", "post"], detail=False)
    def credential(self, request, *args, **kwargs):
        user = self.request.user
        if request.method == "GET":
            user_backup_credentials_data = []
            if not user or isinstance(user, AnonymousUser):
                email = self.request.query_params.get("email")
                if not email:
                    raise NotFound
                try:
                    user = self.user_service.retrieve_by_email(email=email)
                except UserDoesNotExistException:
                    raise NotFound
            user_backup_credentials = self.backup_credential_service.list_backup_credentials(**{
                "user_id": user.user_id
            })
            for backup_credential in user_backup_credentials:
                user_backup_credentials_data.append({
                    "credential_id": backup_credential.fd_credential_id,
                    "random": backup_credential.fd_random
                })
            return Response(status=status.HTTP_200_OK, data={
                "credential_id": user.fd_credential_id,
                "random": user.fd_random,
                "backup_keys": user_backup_credentials_data
            })

        elif request.method == "POST":
            # Saving the cred id of the user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            credential_id = validated_data.get("credential_id")
            credential_random = random.randbytes(16).hex()
            user = self.user_service.update_passwordless_cred(
                user=user, fd_credential_id=credential_id, fd_random=credential_random
            )
            return Response(status=status.HTTP_200_OK, data={
                "credential_id": user.fd_credential_id,
                "random": user.fd_random
            })
