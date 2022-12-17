from rest_framework.response import Response
from rest_framework.decorators import action

from shared.permissions.locker_permissions.import_pwd_permission import ImportPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_VAULT
from v1_0.import_data.serializers import ImportFolderSerializer, ImportCipherSerializer
from v1_0.general_view import PasswordManagerViewSet


class ImportDataPwdViewSet(PasswordManagerViewSet):
    permission_classes = (ImportPwdPermission, )
    http_method_names = ["head", "options", "post"]

    def get_serializer_class(self):
        if self.action == "import_folders":
            self.serializer_class = ImportFolderSerializer
        elif self.action == "import_ciphers":
            self.serializer_class = ImportCipherSerializer
        return super(ImportDataPwdViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def import_folders(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        folders = validated_data.get("folders", [])
        folder_ids = self.folder_repository.import_multiple_folders(user=user, folders=folders)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id]).send()

        return Response(status=200, data={"ids": folder_ids})

    @action(methods=["post"], detail=False)
    def import_ciphers(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        ciphers = validated_data.get("ciphers", [])
        allow_cipher_type = self.user_repository.get_max_allow_cipher_type(user=user)

        self.cipher_repository.import_multiple_ciphers(user=user, ciphers=ciphers, allow_cipher_type=allow_cipher_type)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id]).send()
        return Response(status=200, data={"success": True})

