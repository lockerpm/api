from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.backup_credential_pwd_permission import \
    BackupCredentialPwdPermission
from locker_server.core.exceptions.backup_credential_exception import BackupCredentialDoesNotExistException, \
    BackupCredentialMaximumReachedException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.error_responses.error import gen_error

from .serializers import *


class BackupCredentialPwdViewSet(APIBaseViewSet):
    permission_classes = (BackupCredentialPwdPermission,)
    http_method_names = ["options", "head", "get", "post", "put", "delete"]

    def get_throttles(self):
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListBackupCredentialSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailBackupCredentialSerializer
        elif self.action == "create":
            self.serializer_class = CreateBackupCredentialSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        backup_credentials = self.backup_credential_service.list_backup_credentials(**{
            "user_id": user.user_id
        })
        return backup_credentials

    def get_object(self):
        try:
            backup_credential = self.backup_credential_service.get_by_id(
                backup_credential_id=self.kwargs.get("pk")
            )
            self.check_object_permissions(request=self.request, obj=backup_credential)
        except BackupCredentialDoesNotExistException:
            raise NotFound
        return backup_credential

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10

        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        keys = validated_data.get("keys", {})
        try:
            new_backup_credential = self.backup_credential_service.create_backup_credential(
                current_user=user,
                keys=keys,
                backup_credential_create_data=validated_data
            )
        except UserDoesNotExistException:
            raise NotFound
        except BackupCredentialMaximumReachedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("10000")]})
        return Response(
            status=status.HTTP_201_CREATED,
            data={
                "id": new_backup_credential.backup_credential_id
            }
        )

    def destroy(self, request, *args, **kwargs):
        backup_credential = self.get_object()
        try:
            self.backup_credential_service.delete_backup_credential(
                backup_credential_id=backup_credential.backup_credential_id
            )
        except BackupCredentialDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_204_NO_CONTENT)
