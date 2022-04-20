import json

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from core.utils.data_helpers import camel_snake_data
from shared.background import BG_EVENT, LockerBackgroundFactory
from shared.constants.event import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.cipher_pwd_permission import CipherPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_VAULT
from v1_0.ciphers.serializers import VaultItemSerializer, UpdateVaultItemSerializer, \
    MutipleItemIdsSerializer, MultipleMoveSerializer, ShareVaultItemSerializer, ImportCipherSerializer, \
    SyncOfflineCipherSerializer, DetailCipherSerializer
from v1_0.apps import PasswordManagerViewSet


class CipherPwdViewSet(PasswordManagerViewSet):
    permission_classes = (CipherPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["vaults"]:
            self.serializer_class = VaultItemSerializer
        elif self.action in ["retrieve"]:
            self.serializer_class = DetailCipherSerializer
        elif self.action in ["update"]:
            self.serializer_class = UpdateVaultItemSerializer
        elif self.action in ["share"]:
            self.serializer_class = ShareVaultItemSerializer
        elif self.action in ["multiple_delete", "multiple_restore", "multiple_permanent_delete"]:
            self.serializer_class = MutipleItemIdsSerializer
        elif self.action in ["multiple_move"]:
            self.serializer_class = MultipleMoveSerializer
        elif self.action in ["import_data"]:
            self.serializer_class = ImportCipherSerializer
        elif self.action in ["sync_offline"]:
            self.serializer_class = SyncOfflineCipherSerializer
        return super(CipherPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            cipher = self.cipher_repository.get_by_id(cipher_id=self.kwargs.get("pk"))
            if cipher.team:
                self.check_object_permissions(request=self.request, obj=cipher)
            else:
                if cipher.user != self.request.user:
                    raise NotFound
            return cipher
        except ObjectDoesNotExist:
            raise NotFound

    @action(methods=["post"], detail=False)
    def vaults(self, request, *args, **kwargs):
        ip = request.data.get("ip")
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.validated_data.get("team")
        cipher_detail = serializer.save(**{"check_plan": True})
        cipher_detail.pop("team", None)
        cipher_detail = json.loads(json.dumps(cipher_detail))

        # We create new cipher object from cipher detail data.
        # Then, we update revision date of user (personal or members of the organization)
        # If cipher belongs to the organization, we also update collections of the cipher.
        new_cipher = self.cipher_repository.save_new_cipher(cipher_data=cipher_detail)
        # Send sync message
        PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[request.user.user_id], team=team, add_all=True).send(
            data={"id": str(new_cipher.id)}
        )
        # Create event
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
            "team_id": new_cipher.team_id, "user_id": user.user_id, "acting_user_id": user.user_id,
            "type": EVENT_CIPHER_CREATED, "cipher_id": new_cipher.id, "ip_address": ip
        })
        return Response(status=200, data={"id": new_cipher.id})

    @action(methods=["put"], detail=False)
    def multiple_delete(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Check permission of user and update deleted_date of the ciphers here
        deleted_cipher_ids = self.cipher_repository.delete_multiple_cipher(
            cipher_ids=cipher_ids, user_deleted=request.user
        )
        # Sync event
        deleted_ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=deleted_cipher_ids)
        teams = self.team_repository.get_multiple_team_by_ids(deleted_ciphers.values_list('team_id', flat=True))
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id], teams=teams, add_all=True).send()

        # Log: team's event
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_ciphers", **{
        #     "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_CIPHER_SOFT_DELETED, "ciphers": deleted_ciphers, "ip_address": ip
        # })

        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def multiple_permanent_delete(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Check permission of user here
        ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=cipher_ids)
        teams = self.team_repository.get_multiple_team_by_ids(ciphers.values_list('team_id', flat=True))
        # We will get list ciphers of user (personal ciphers and managed ciphers)
        # Then delete all them and bump revision date of users
        # Finally, we send sync event to all relational users
        self.cipher_repository.delete_permanent_multiple_cipher(cipher_ids=cipher_ids, user_deleted=request.user)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id], teams=teams, add_all=True).send()

        # Log: Team's event
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_ciphers", **{
        #     "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_CIPHER_DELETED, "ciphers": ciphers, "ip_address": ip
        # })
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def multiple_restore(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # We will check permission and set deleted_date of cipher to null
        # Then bump revision date of users and send sync event to all relational users
        restored_cipher_ids = self.cipher_repository.restore_multiple_cipher(
            cipher_ids=cipher_ids, user_restored=request.user
        )
        # Sync event
        restored_ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=restored_cipher_ids)
        teams = self.team_repository.get_multiple_team_by_ids(list(restored_ciphers.values_list('team_id', flat=True)))
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id], teams=teams, add_all=True).send()

        # Log: team's event
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_ciphers", **{
        #     "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_CIPHER_RESTORE, "ciphers": ciphers, "ip_address": ip
        # })
        return Response(status=200, data={"success": True})

    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        cipher_obj = self.cipher_repository.get_multiple_by_user(
            user=user, filter_ids=[cipher.id]
        ).prefetch_related('collections_ciphers').first()
        serializer = DetailCipherSerializer(cipher_obj, context={"user": user}, many=False)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=200, data=result)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.validated_data.get("team")
        cipher_detail = serializer.save(**{"cipher": cipher})
        cipher_detail.pop("team", None)
        cipher_detail = json.loads(json.dumps(cipher_detail))
        cipher = self.cipher_repository.save_update_cipher(cipher=cipher, cipher_data=cipher_detail)
        PwdSync(
            event=SYNC_EVENT_CIPHER_UPDATE,
            user_ids=[request.user.user_id],
            team=team,
            add_all=True
        ).send(data={"id": cipher.id})
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
            "team_id": cipher.team_id, "user_id": user.user_id, "acting_user_id": user.user_id,
            "type": EVENT_CIPHER_UPDATED, "cipher_id": cipher.id, "ip_address": ip
        })
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
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id]).send()
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def import_data(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        ciphers = validated_data.get("ciphers", [])
        folders = validated_data.get("folders", [])
        folder_relationships = validated_data.get("folderRelationships", [])
        allow_cipher_type = self.user_repository.get_max_allow_cipher_type(user=user)
        self.cipher_repository.import_multiple_cipher(
            user, ciphers, folders, folder_relationships, allow_cipher_type=allow_cipher_type
        )
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id]).send()
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def sync_offline(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        ciphers = validated_data.get("ciphers", [])
        folders = validated_data.get("folders", [])
        folder_relationships = validated_data.get("folderRelationships", [])
        self.cipher_repository.sync_personal_cipher_offline(user, ciphers, folders, folder_relationships)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id]).send()
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def share(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        if cipher.team_id:
            raise ValidationError({"non_field_errors": [gen_error("5000")]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.validated_data.get("team")
        cipher_detail = serializer.save()
        cipher_detail.pop("team", None)
        cipher_detail = json.loads(json.dumps(cipher_detail))
        cipher = self.cipher_repository.save_share_cipher(cipher=cipher, cipher_data=cipher_detail)
        PwdSync(
            event=SYNC_EVENT_CIPHER_UPDATE,
            user_ids=[request.user.user_id],
            team=team,
            add_all=True
        ).send(data={"id": cipher.id})
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
            "team_id": cipher.team_id, "user_id": user.user_id, "acting_user_id": user.user_id,
            "type": EVENT_CIPHER_SHARED, "cipher_id": cipher.id, "ip_address": ip
        })
        return Response(status=200, data={"id": cipher.id})

    @action(methods=["get"], detail=False)
    def share_members(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        cipher_members = self.cipher_repository.get_cipher_members(cipher=cipher)
        return Response(status=200, data=cipher_members)
