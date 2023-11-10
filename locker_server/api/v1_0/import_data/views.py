from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.import_pwd_permission import ImportPwdPermission
from locker_server.shared.external_services.pm_sync import PwdSync, SYNC_EVENT_VAULT
from .serializers import ImportFolderSerializer, ImportCipherSerializer


class ImportDataPwdViewSet(APIBaseViewSet):
    permission_classes = (ImportPwdPermission, )
    http_method_names = ["head", "options", "post"]

    def get_serializer_class(self):
        if self.action == "import_folders":
            self.serializer_class = ImportFolderSerializer
        elif self.action == "import_ciphers":
            self.serializer_class = ImportCipherSerializer
        return super().get_serializer_class()

    @action(methods=["post"], detail=False)
    def import_folders(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        folders = validated_data.get("folders", [])

        folder_ids = self.folder_service.import_multiple_folders(user_id=user.user_id, folders=folders)
        self.user_service.delete_sync_cache_data(user_id=user.user_id)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[user.user_id]).send()
        return Response(status=status.HTTP_200_OK, data={"ids": folder_ids})

    @action(methods=["post"], detail=False)
    def import_ciphers(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        ciphers = validated_data.get("ciphers", [])

        self.cipher_service.import_multiple_ciphers(user=user, ciphers=ciphers)
        self.user_service.delete_sync_cache_data(user_id=user.user_id)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[user.user_id]).send()
        return Response(status=status.HTTP_200_OK, data={"success": True})
