from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from core.utils.data_helpers import camel_snake_data
from shared.permissions.locker_permissions.folder_pwd_permission import FolderPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_FOLDER_UPDATE, SYNC_EVENT_FOLDER_DELETE
from v1_0.folders.serializers import FolderSerializer, DetailFolderSerializer
from v1_0.apps import PasswordManagerViewSet


class FolderPwdViewSet(PasswordManagerViewSet):
    permission_classes = (FolderPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    serializer_class = FolderSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            self.serializer_class = DetailFolderSerializer
        return super(FolderPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            folder = self.folder_repository.get_by_id(folder_id=self.kwargs.get("pk"), user=self.request.user)
            return folder
        except ObjectDoesNotExist:
            raise NotFound

    def create(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        name = validated_data.get("name")

        # We create new folder object from folder data
        # Then we update revision date of user
        new_folder = self.folder_repository.save_new_folder(user=user, name=name)
        PwdSync(event=SYNC_EVENT_FOLDER_UPDATE, user_ids=[request.user.user_id]).send(data={"id": str(new_folder.id)})
        return Response(status=200, data={"id": new_folder.id})

    def retrieve(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        folder = self.get_object()
        serializer = self.get_serializer(folder)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=200, data=result)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        folder = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        name = validated_data.get("name", folder.name)
        folder = self.folder_repository.save_update_folder(user=user, folder=folder, name=name)
        PwdSync(event=SYNC_EVENT_FOLDER_UPDATE, user_ids=[request.user.user_id]).send(data={"id": str(folder.id)})
        return Response(status=200, data={"id": folder.id})

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        folder = self.get_object()
        folder_id = kwargs.get("pk")
        user_id = user.user_id
        # Get list cipher of this folder then re-set folder of cipher
        ciphers = self.cipher_repository.get_multiple_by_user(user=user)
        soft_delete_cipher = []
        for cipher in ciphers:
            folders_dict = cipher.get_folders()
            cipher_folder_id = folders_dict.get(user_id, None)
            if cipher_folder_id == folder_id:
                folders_dict[user_id] = None
                cipher.folders = folders_dict
                cipher.save()
                if not cipher.team_id:
                    soft_delete_cipher.append(cipher.id)
        # Soft delete all ciphers in folder
        self.cipher_repository.delete_multiple_cipher(cipher_ids=soft_delete_cipher, user_deleted=user)
        # Delete this folder object
        folder.delete()
        # Sending sync event
        PwdSync(event=SYNC_EVENT_FOLDER_DELETE, user_ids=[request.user.user_id]).send()
        return Response(status=204)
