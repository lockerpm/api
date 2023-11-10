import json

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.cipher_pwd_permission import CipherPwdPermission
from locker_server.api.v1_0.sync.serializers import SyncCipherSerializer
from locker_server.core.exceptions.cipher_exception import *
from locker_server.core.exceptions.collection_exception import CollectionDoesNotExistException, \
    CollectionCannotRemoveException, CollectionCannotAddException
from locker_server.core.exceptions.team_exception import TeamLockedException, TeamDoesNotExistException
from locker_server.core.exceptions.team_member_exception import OnlyAllowOwnerUpdateException
from locker_server.shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD, IMMUTABLE_CIPHER_TYPES
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_CIPHER
from locker_server.shared.external_services.pm_sync import SYNC_EVENT_FOLDER_UPDATE, PwdSync, SYNC_EVENT_FOLDER_DELETE, \
    SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_CIPHER_DELETE_PERMANENT, SYNC_EVENT_VAULT
from locker_server.shared.utils.app import camel_snake_data
from locker_server.shared.utils.avatar import get_avatar
from .serializers import VaultItemSerializer, MultipleItemIdsSerializer, DetailCipherSerializer, \
    UpdateVaultItemSerializer, UpdateCipherUseSerializer, MultipleMoveSerializer, SyncOfflineCipherSerializer


class CipherPwdViewSet(APIBaseViewSet):
    permission_classes = (CipherPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["vaults"]:
            self.serializer_class = VaultItemSerializer
        elif self.action in ["retrieve"]:
            self.serializer_class = DetailCipherSerializer
        elif self.action in ["update"]:
            self.serializer_class = UpdateVaultItemSerializer
        elif self.action in ["multiple_delete", "multiple_restore", "multiple_permanent_delete"]:
            self.serializer_class = MultipleItemIdsSerializer
        elif self.action in ["cipher_use"]:
            self.serializer_class = UpdateCipherUseSerializer
        elif self.action in ["multiple_move"]:
            self.serializer_class = MultipleMoveSerializer
        elif self.action in ["sync_offline"]:
            self.serializer_class = SyncOfflineCipherSerializer
        return super().get_serializer_class()

    def get_object(self):
        try:
            cipher = self.cipher_service.get_by_id(cipher_id=self.kwargs.get("pk"))
            if cipher.team:
                self.check_object_permissions(request=self.request, obj=cipher)
            else:
                if cipher.user.user_id != self.request.user.user_id:
                    raise NotFound
            return cipher
        except CipherDoesNotExistException:
            raise NotFound

    @action(methods=["post"], detail=False)
    def vaults(self, request, *args, **kwargs):
        ip = self.get_ip()
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cipher_detail = serializer.save()
        cipher_detail = json.loads(json.dumps(cipher_detail))

        new_cipher = self._create_new_cipher(cipher_data=cipher_detail, check_plan=True)
        # Clear sync data
        self.user_service.delete_sync_cache_data(user_id=user.user_id)
        # Send sync message
        PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id], team=new_cipher.team, add_all=True).send(
            data={"id": str(new_cipher.cipher_id)}
        )
        return Response(status=status.HTTP_200_OK, data={"id": new_cipher.cipher_id})

    def _create_new_cipher(self, cipher_data, check_plan=True):
        try:
            master_pwd_item_obj = self.cipher_service.get_master_pwd_item(user_id=self.request.user.user_id)
            if cipher_data.get("type") in [CIPHER_TYPE_MASTER_PASSWORD] and master_pwd_item_obj:
                raise ValidationError(detail={"type": ["This type is not valid"]})
            new_cipher = self.cipher_service.create_cipher(
                user=self.request.user, cipher_data=cipher_data, check_plan=check_plan
            )
            return new_cipher
        except FolderDoesNotExistException:
            raise ValidationError(detail={"folderId": ["This folder does not exist"]})
        except TeamDoesNotExistException:
            raise ValidationError(detail={"organizationId": [
                "This team does not exist", "Team này không tồn tại"
            ]})
        except TeamLockedException:
            raise ValidationError({"non_field_errors": [gen_error("3003")]})
        except CollectionDoesNotExistException as e:
            raise ValidationError(detail={
                "collectionIds": ["The team collection id {} does not exist".format(e.collection_id)]
            })
        except CipherMaximumReachedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("5002")]})

    @action(methods=["put"], detail=False)
    def multiple_delete(self, request, *args, **kwargs):
        ip = self.get_ip()
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Clear sync data
        self.user_service.delete_sync_cache_data(user_id=user.user_id)
        # Check permission of user and update deleted_date of the ciphers here
        BackgroundFactory.get_background(bg_name=BG_CIPHER).run(func_name="multiple_delete", **{
            "cipher_ids": cipher_ids, "user": user
        })

        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["put"], detail=False)
    def multiple_permanent_delete(self, request, *args, **kwargs):
        ip = self.get_ip()
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Check permission of user here
        ciphers = self.cipher_service.get_multiple_by_ids(cipher_ids=cipher_ids)
        teams = [cipher.team for cipher in ciphers if cipher.team]
        # We will get list ciphers of user (personal ciphers and managed ciphers)
        # Then delete all them and bump revision date of users
        # Finally, we send sync event to all relational users
        deleted_cipher_ids = self.cipher_service.delete_permanent_multiple_cipher(
            cipher_ids=cipher_ids, user_id_deleted=user.user_id
        )
        self.user_service.delete_sync_cache_data(user_id=user.user_id)
        PwdSync(
            event=SYNC_EVENT_CIPHER_DELETE_PERMANENT, user_ids=[request.user.user_id], teams=teams, add_all=True
        ).send(data={"ids": deleted_cipher_ids})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["put"], detail=False)
    def multiple_restore(self, request, *args, **kwargs):
        ip = self.get_ip()
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Clear sync data
        self.user_service.delete_sync_cache_data(user_id=user.user_id)
        # We will check permission and set deleted_date of cipher to null
        # Then bump revision date of users and send sync event to all relational users
        BackgroundFactory.get_background(bg_name=BG_CIPHER).run(func_name="multiple_restore", **{
            "cipher_ids": cipher_ids, "user": request.user
        })
        return Response(status=status.HTTP_200_OK, data={"success": True})

    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()

        try:
            cipher_obj = self.cipher_service.get_multiple_by_user(
                user_id=user.user_id, filter_ids=[cipher.cipher_id]
            )[0]
        except IndexError:
            raise NotFound

        serializer = DetailCipherSerializer(cipher_obj, context={"user": user}, many=False)
        data = serializer.data
        if cipher.team and cipher.team.personal_share is True:
            shared_members = self.sharing_service.get_shared_members(
                personal_shared_team=cipher.team, exclude_owner=False
            )
            sharing_members_data = []
            for member in shared_members:
                member_data = {
                    "id": member.team_member_id,
                    "access_time": member.access_time,
                    "role": member.role.name,
                    "status": member.status,
                    "hide_passwords": member.hide_passwords,
                    "share_type": self.sharing_service.get_personal_share_type(member=member),
                    "pwd_user_id": member.user.internal_id if member.user else None,
                }
                if member.user is not None:
                    member_data["email"] = member.user.email
                    member_data["full_name"] = member.user.full_name
                    member_data["username"] = member.user.username
                    member_data["avatar"] = member.user.get_avatar()
                else:
                    member_data["email"] = member.email
                    member_data["avatar"] = get_avatar(member.email)
            data["sharing"] = sharing_members_data
        else:
            data["sharing"] = []
        result = camel_snake_data(data, snake_to_camel=True)
        return Response(status=200, data=result)

    def update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        if cipher.cipher_type in IMMUTABLE_CIPHER_TYPES:
            raise PermissionDenied
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cipher_detail = serializer.save()
        cipher_detail = json.loads(json.dumps(cipher_detail))
        cipher = self._update_cipher(cipher_obj=cipher, cipher_data=cipher_detail)
        self.user_service.delete_sync_cache_data(user_id=request.user.user_id)
        PwdSync(
            event=SYNC_EVENT_CIPHER_UPDATE,
            user_ids=[request.user.user_id],
            team=cipher.team,
            add_all=True
        ).send(data={"id": cipher.cipher_id})
        data = SyncCipherSerializer(cipher, many=False, context={"user": request.user}).data
        return Response(status=status.HTTP_200_OK, data=camel_snake_data(data, snake_to_camel=True))

    def _update_cipher(self, cipher_obj, cipher_data):
        try:
            return self.cipher_service.update_cipher(
                cipher=cipher_obj, user=self.request.user, cipher_data=cipher_data, view_action="update"
            )
        except FolderDoesNotExistException:
            raise ValidationError(detail={"folderId": ["This folder does not exist"]})
        except TeamDoesNotExistException:
            raise ValidationError(detail={"organizationId": [
                "This team does not exist", "Team này không tồn tại"
            ]})
        except TeamLockedException:
            raise ValidationError({"non_field_errors": [gen_error("3003")]})
        except CollectionCannotRemoveException as e:
            raise ValidationError(detail={"collectionIds": [
                f"You can not remove collection {e.collection_id}"
            ]})
        except CollectionCannotAddException as e:
            raise ValidationError(detail={"collectionIds": [
                f"You can not add collection {e.collection_id}"
            ]})
        except OnlyAllowOwnerUpdateException:
            raise ValidationError(detail={
                "organizationId": ["You must be owner of the item to change this field"]
            })
        except CipherMaximumReachedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("5002")]})

    @action(methods=["put"], detail=False)
    def cipher_use(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        cipher = self.get_object()
        if cipher.cipher_type in IMMUTABLE_CIPHER_TYPES:
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
        try:
            cipher = self.cipher_service.update_cipher_use(cipher=cipher, cipher_use_data=cipher_use_data)
        except CipherDoesNotExistException:
            raise NotFound
        PwdSync(
            event=SYNC_EVENT_CIPHER_UPDATE,
            user_ids=[user.user_id],
            team=cipher.team,
            add_all=True
        ).send(data={"id": cipher.id})
        data = SyncCipherSerializer(cipher, many=False, context={"user": request.user}).data
        return Response(status=status.HTTP_200_OK, data=camel_snake_data(data, snake_to_camel=True))

    @action(methods=["put"], detail=False)
    def multiple_move(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")
        folder_id = validated_data.get("folderId")

        try:
            moved_cipher_ids = self.cipher_service.move_multiple_cipher(
                cipher_ids=cipher_ids, user_id_moved=self.request.user.user_id, folder_id=folder_id
            )
        except FolderDoesNotExistException:
            raise ValidationError(detail={"folderId": ["This folder does not exist"]})
        self.user_service.delete_sync_cache_data(user_id=request.user.user_id)
        PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[request.user.user_id]).send(
            data={"ids": moved_cipher_ids}
        )
        return Response(status=status.HTTP_200_OK, data={"success": True})

    # ----------------- (DEPRECATED) ---------------------- #
    @action(methods=["post"], detail=False)
    def import_data(self, request, *args, **kwargs):
        raise NotFound
        # user = self.request.user
        # self.check_pwd_session_auth(request=request)
        # delete_sync_cache_data(user_id=user.user_id)
        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # validated_data = serializer.validated_data
        # ciphers = validated_data.get("ciphers", [])
        # folders = validated_data.get("folders", [])
        # folder_relationships = validated_data.get("folderRelationships", [])
        # allow_cipher_type = self.user_repository.get_max_allow_cipher_type(user=user)
        # self.cipher_repository.import_multiple_cipher(
        #     user, ciphers, folders, folder_relationships, allow_cipher_type=allow_cipher_type
        # )
        # PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id]).send()
        # return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def sync_offline(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        self.user_service.delete_sync_cache_data(user_id=user.user_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        ciphers = validated_data.get("ciphers", [])
        folders = validated_data.get("folders", [])
        folder_relationships = validated_data.get("folderRelationships", [])
        self.cipher_service.sync_personal_cipher_offline(
            user=user, ciphers=ciphers, folders=folders, folder_relationships=folder_relationships
        )
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[user.user_id]).send()
        return Response(status=status.HTTP_200_OK, data={"success": True})
