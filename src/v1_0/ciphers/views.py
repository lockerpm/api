from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

from shared.permissions.locker_permissions.cipher_pwd_permission import CipherPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_DELETE, SYNC_EVENT_CIPHER_CREATE
from v1_0.ciphers.serializers import VaultItemSerializer, UpdateVaultItemSerializer, \
    MutipleItemIdsSerializer, MultipleMoveSerializer
from v1_0.apps import PasswordManagerViewSet


class CipherPwdViewSet(PasswordManagerViewSet):
    permission_classes = (CipherPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["vaults", "share"]:
            self.serializer_class = VaultItemSerializer
        elif self.action in ["update"]:
            self.serializer_class = UpdateVaultItemSerializer
        elif self.action in ["multiple_delete", "multiple_restore", "multiple_permanent_delete"]:
            self.serializer_class = MutipleItemIdsSerializer
        elif self.action in ["multiple_move"]:
            self.serializer_class = MultipleMoveSerializer
        return super(CipherPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            cipher = self.cipher_repository.get_by_id(cipher_id=self.kwargs.get("pk"))
            # self.check_object_permissions(request=self.request, obj=cipher)
            return cipher
        except ObjectDoesNotExist:
            raise NotFound

    @action(methods=["post"], detail=False)
    def vaults(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cipher_detail = serializer.save()

        # We create new cipher object from cipher detail data.
        # Then, we update revision date of user (personal or members of the organization)
        # If cipher belongs to the organization, we also update collections of the cipher.
        new_cipher = self.cipher_repository.save_new_cipher(cipher_data=cipher_detail)
        PwdSync(
            event=SYNC_EVENT_CIPHER_CREATE,
            user_ids=[request.user.user_id],
            team=serializer.validated_data.get("team"),
            add_all=True
        ).send()
        return Response(status=200, data={"id": new_cipher.id})

    @action(methods=["put"], detail=False)
    def multiple_delete(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Check permission of user here
        ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=cipher_ids)
        teams = self.team_repository.get_multiple_team_by_ids(ciphers.values_list('team_id', flat=True))
        for team in teams:
            self.check_object_permissions(request=request, obj=team)
        self.cipher_repository.delete_multiple_cipher(cipher_ids=cipher_ids, user_deleted=request.user)
        PwdSync(event=SYNC_EVENT_CIPHER_DELETE, user_ids=[request.user.user_id], teams=teams, add_all=True).send()
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def multiple_permanent_delete(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Check permission of user here
        ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=cipher_ids)
        teams = self.team_repository.get_multiple_team_by_ids(ciphers.values_list('team_id', flat=True))
        for team in teams:
            self.check_object_permissions(request=request, obj=team)
        # We will get list ciphers of user (personal ciphers and managed ciphers)
        # Then delete all them and bump revision date of users
        # Finally, we send sync event to all relational users
        self.cipher_repository.delete_permanent_multiple_cipher(cipher_ids=cipher_ids, user_deleted=request.user)
        PwdSync(event=SYNC_EVENT_CIPHER_DELETE, user_ids=[request.user.user_id], teams=teams, add_all=True).send()
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def multiple_restore(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Check permission of user here
        ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=cipher_ids)
        teams = self.team_repository.get_multiple_team_by_ids(ciphers.values_list('team_id', flat=True))
        for team in teams:
            self.check_object_permissions(request=request, obj=team)
        # We will set deleted_date of cipher to null
        # Then bump revision date of users and send sync event to all relational users
        self.cipher_repository.restore_multiple_cipher(cipher_ids=cipher_ids, user_restored=request.user)
        PwdSync(event=SYNC_EVENT_CIPHER_DELETE, user_ids=[request.user.user_id], teams=teams, add_all=True).send()
        return Response(status=200, data={"success": True})

    def update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cipher_detail = serializer.save(**{"cipher": cipher})
        cipher = self.cipher_repository.save_update_cipher(cipher=cipher, cipher_data=cipher_detail)
        PwdSync(
            event=SYNC_EVENT_CIPHER_CREATE,
            user_ids=[request.user.user_id],
            team=serializer.validated_data.get("team"),
            add_all=True
        ).send()
        return Response(status=200, data={"id": cipher.id})

    @action(methods=["put"], detail=False)
    def multiple_move(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")
        folder_id = validated_data.get("folderId")

        self.cipher_repository.move_multiple_cipher(cipher_ids=cipher_ids, user_moved=request.user, folder_id=folder_id)
        PwdSync(event=SYNC_EVENT_CIPHER_DELETE, user_ids=[request.user.user_id]).send()
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def import_data(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def share(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        return Response(status=200, data={"success": True})
