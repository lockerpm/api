import json

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from core.utils.data_helpers import camel_snake_data
from shared.background import LockerBackgroundFactory, BG_CIPHER
from shared.caching.sync_cache import delete_sync_cache_data
from shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD, IMMUTABLE_CIPHER_TYPES
from shared.permissions.locker_permissions.cipher_pwd_permission import CipherPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_VAULT, \
    SYNC_EVENT_CIPHER_DELETE_PERMANENT
from v1_0.ciphers.serializers import VaultItemSerializer, UpdateVaultItemSerializer, \
    MutipleItemIdsSerializer, MultipleMoveSerializer, ShareVaultItemSerializer, ImportCipherSerializer, \
    SyncOfflineCipherSerializer, DetailCipherSerializer, UpdateCipherUseSerializer
from v1_0.sync.serializers import SyncCipherSerializer
from v1_0.general_view import PasswordManagerViewSet


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
        elif self.action in ["cipher_use"]:
            self.serializer_class = UpdateCipherUseSerializer
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

        if cipher_detail.get("type") in [CIPHER_TYPE_MASTER_PASSWORD] and \
                user.created_ciphers.filter(type=CIPHER_TYPE_MASTER_PASSWORD).exists():
            raise ValidationError(detail={"type": ["This type is not valid"]})

        # We create new cipher object from cipher detail data.
        # Then, we update revision date of user (personal or members of the organization)
        # If cipher belongs to the organization, we also update collections of the cipher.
        new_cipher = self.cipher_repository.save_new_cipher(cipher_data=cipher_detail)
        # Clear sync data
        delete_sync_cache_data(user_id=user.user_id)
        # Send sync message
        PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id], team=team, add_all=True).send(
            data={"id": str(new_cipher.id)}
        )
        # Create event
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
        #     "team_id": new_cipher.team_id, "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_CIPHER_CREATED, "cipher_id": new_cipher.id, "ip_address": ip
        # })
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

        # Clear sync data
        delete_sync_cache_data(user_id=user.user_id)

        # Check permission of user and update deleted_date of the ciphers here
        LockerBackgroundFactory.get_background(bg_name=BG_CIPHER).run(func_name="multiple_delete", **{
            "cipher_ids": cipher_ids, "user": request.user
        })

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
        deleted_cipher_ids = self.cipher_repository.delete_permanent_multiple_cipher(
            cipher_ids=cipher_ids, user_deleted=request.user
        )
        delete_sync_cache_data(user_id=user.user_id)
        PwdSync(
            event=SYNC_EVENT_CIPHER_DELETE_PERMANENT, user_ids=[request.user.user_id], teams=teams, add_all=True
        ).send(data={"ids": deleted_cipher_ids})

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

        # Clear sync data
        delete_sync_cache_data(user_id=user.user_id)
        # We will check permission and set deleted_date of cipher to null
        # Then bump revision date of users and send sync event to all relational users
        LockerBackgroundFactory.get_background(bg_name=BG_CIPHER).run(func_name="multiple_restore", **{
            "cipher_ids": cipher_ids, "user": request.user
        })

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
        data = serializer.data
        if cipher.team and cipher.team.personal_share is True:
            shared_members = self.sharing_repository.get_shared_members(
                personal_shared_team=cipher.team, exclude_owner=False
            )
            data["sharing"] = [{
                "id": member.id,
                "access_time": member.access_time,
                "user_id": member.user_id,
                "email": member.email,
                "role": member.role_id,
                "status": member.status,
                "hide_passwords": member.hide_passwords,
                "share_type": self.sharing_repository.get_personal_share_type(member=member),
                "pwd_user_id": member.user.internal_id if member.user else None
            } for member in shared_members]

        else:
            data["sharing"] = []
        result = camel_snake_data(data, snake_to_camel=True)
        return Response(status=200, data=result)

    def update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        if cipher.type in IMMUTABLE_CIPHER_TYPES:
            raise PermissionDenied
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cipher_detail = serializer.save(**{"cipher": cipher})
        cipher_detail.pop("team", None)
        cipher_detail = json.loads(json.dumps(cipher_detail))
        cipher = self.cipher_repository.save_update_cipher(cipher=cipher, cipher_data=cipher_detail)
        delete_sync_cache_data(user_id=request.user.user_id)
        PwdSync(
            event=SYNC_EVENT_CIPHER_UPDATE,
            user_ids=[request.user.user_id],
            team=cipher.team,
            add_all=True
        ).send(data={"id": cipher.id})
        data = SyncCipherSerializer(cipher, many=False, context={"user": request.user}).data
        return Response(status=200, data=camel_snake_data(data, snake_to_camel=True))

    @action(methods=["put"], detail=False)
    def cipher_use(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        if cipher.type in IMMUTABLE_CIPHER_TYPES:
            raise PermissionDenied
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_use_data = {
            "favorite": validated_data.get("favorite"),
            "use": validated_data.get("use"),
            "user_id": user.user_id
        }
        cipher = self.cipher_repository.save_cipher_use(cipher=cipher, cipher_use_data=cipher_use_data)
        PwdSync(
            event=SYNC_EVENT_CIPHER_UPDATE,
            user_ids=[user.user_id],
            team=cipher.team,
            add_all=True
        ).send(data={"id": cipher.id})
        data = SyncCipherSerializer(cipher, many=False, context={"user": request.user}).data
        return Response(status=200, data=camel_snake_data(data, snake_to_camel=True))

    @action(methods=["put"], detail=False)
    def multiple_move(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")
        folder_id = validated_data.get("folderId")

        self.cipher_repository.move_multiple_cipher(cipher_ids=cipher_ids, user_moved=request.user, folder_id=folder_id)
        delete_sync_cache_data(user_id=request.user.user_id)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id]).send()
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def import_data(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        delete_sync_cache_data(user_id=user.user_id)
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
        delete_sync_cache_data(user_id=user.user_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        ciphers = validated_data.get("ciphers", [])
        folders = validated_data.get("folders", [])
        folder_relationships = validated_data.get("folderRelationships", [])
        self.cipher_repository.sync_personal_cipher_offline(user, ciphers, folders, folder_relationships)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id]).send()
        return Response(status=200, data={"success": True})
