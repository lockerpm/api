import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Count
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models import Enterprise
from cystack_models.models.notifications.notification_settings import NotificationSetting
from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.caching.sync_cache import delete_sync_cache_data
from shared.constants.ciphers import MAP_CIPHER_TYPE_STR
from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from shared.constants.event import EVENT_ITEM_SHARE_CREATED
from shared.constants.members import *
from shared.constants.user_notification import NOTIFY_SHARING
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.sharing_pwd_permission import SharingPwdPermission
from shared.services.fcm.constants import FCM_TYPE_NEW_SHARE, FCM_TYPE_CONFIRM_SHARE, FCM_TYPE_REJECT_SHARE, \
    FCM_TYPE_ACCEPT_SHARE, FCM_TYPE_NEW_SHARE_AFTER_OWNER_CONFIRMED
from shared.services.fcm.fcm_request_entity import FCMRequestEntity
from shared.services.fcm.fcm_sender import FCMSenderService
from shared.services.pm_sync import *
from shared.utils.app import now
from v1_0.sharing.serializers import UserPublicKeySerializer, SharingSerializer, SharingInvitationSerializer, \
    StopSharingSerializer, UpdateInvitationRoleSerializer, MultipleSharingSerializer, UpdateShareFolderSerializer, \
    StopSharingFolderSerializer, AddMemberSerializer, AddItemShareFolderSerializer, UpdateGroupInvitationRoleSerializer, \
    GroupMemberConfirmSerializer
from v1_0.general_view import PasswordManagerViewSet


class SharingPwdViewSet(PasswordManagerViewSet):
    permission_classes = (SharingPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "public_key":
            self.serializer_class = UserPublicKeySerializer
        elif self.action == "share":
            self.serializer_class = SharingSerializer
        elif self.action == "multiple_share":
            self.serializer_class = MultipleSharingSerializer
        elif self.action == "invitations":
            self.serializer_class = SharingInvitationSerializer
        elif self.action in ["stop_share", "stop_group_share", "stop_share_cipher_folder"]:
            self.serializer_class = StopSharingSerializer
        elif self.action == "update_role":
            self.serializer_class = UpdateInvitationRoleSerializer
        elif self.action == "invitation_group_confirm":
            self.serializer_class = GroupMemberConfirmSerializer
        elif self.action == "update_group_role":
            self.serializer_class = UpdateGroupInvitationRoleSerializer
        elif self.action == "update_share_folder":
            self.serializer_class = UpdateShareFolderSerializer
        elif self.action in ["stop_share_folder", "delete_share_folder"]:
            self.serializer_class = StopSharingFolderSerializer
        elif self.action == "add_member":
            self.serializer_class = AddMemberSerializer

        elif self.action in ["add_item_share_folder", "remove_item_share_folder"]:
            self.serializer_class = AddItemShareFolderSerializer
        return super(SharingPwdViewSet, self).get_serializer_class()

    def allow_personal_sharing(self, user):
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        plan_obj = current_plan.get_plan_obj()
        if user.is_active_enterprise_member() is False and plan_obj.allow_personal_share() is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        return user

    def get_personal_share(self, sharing_id):
        try:
            team = self.team_repository.get_by_id(team_id=sharing_id)
            if team.personal_share is False:
                raise NotFound
            self.check_object_permissions(request=self.request, obj=team)
            return team
        except ObjectDoesNotExist:
            raise NotFound

    @action(methods=["post"], detail=False)
    def public_key(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user_id = validated_data.get("user_id")
        try:
            user_obj = self.user_repository.get_by_id(user_id=user_id)
            if not self.user_repository.is_activated(user=user_obj):
                return Response(status=200, data={"public_key": None})
        except ObjectDoesNotExist:
            return Response(status=200, data={"public_key": None})
        return Response(status=200, data={"public_key": user_obj.public_key})

    @action(methods=["get"], detail=False)
    def invitations(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        sharing_invitations = self.user_repository.get_list_invitations(user=user, personal_share=True)
        serializer = self.get_serializer(sharing_invitations, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["put"], detail=False)
    def invitation_update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        user = self.request.user
        status = request.data.get("status")
        if status not in ["accept", "reject"]:
            raise ValidationError(detail={"status": ["This status is not valid"]})
        try:
            sharing_invitation = user.team_members.get(
                id=kwargs.get("pk"), status=PM_MEMBER_STATUS_INVITED,
                team__key__isnull=False, user__activated=True
            )
        except ObjectDoesNotExist:
            raise NotFound

        primary_owner = self.team_repository.get_primary_member(team=sharing_invitation.team)
        shared_type_name = None
        item_id = None
        cipher_id = None
        folder_id = None
        # Accept this invitation
        if status == "accept":
            member = self.sharing_repository.accept_invitation(member=sharing_invitation)
            member_status = member.status
            PwdSync(event=SYNC_EVENT_MEMBER_ACCEPTED, user_ids=[primary_owner.user_id, user.user_id]).send()
            # If share a cipher:
            if sharing_invitation.team.collections.all().exists() is False:
                share_cipher = sharing_invitation.team.ciphers.first()
                if share_cipher:
                    shared_type_name = share_cipher.type
                    item_id = share_cipher.id
                    cipher_id = item_id
                    delete_sync_cache_data(user_id=user.user_id)
                    PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id]).send(data={"id": share_cipher.id})
            # Else, share a folder
            else:
                share_collection = sharing_invitation.team.collections.first()
                if share_collection:
                    shared_type_name = "folder"
                    item_id = share_collection.id
                    folder_id = item_id
                    delete_sync_cache_data(user_id=user.user_id)
                    PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[user.user_id]).send(
                        data={"id": share_collection.id}
                    )

        # Reject this invitation
        else:
            if sharing_invitation.team.collections.all().exists() is False:
                share_cipher = sharing_invitation.team.ciphers.first()
                shared_type_name = share_cipher.type if share_cipher else shared_type_name
                item_id = share_cipher.id if share_cipher else item_id
                cipher_id = item_id
            else:
                shared_type_name = "folder"
                share_collection = sharing_invitation.team.collections.first()
                item_id = share_collection.id if share_collection else item_id
                folder_id = item_id

            self.sharing_repository.reject_invitation(member=sharing_invitation)
            member_status = None
            PwdSync(event=SYNC_EVENT_MEMBER_REJECT, user_ids=[primary_owner.user_id, user.user_id]).send()

        # Push mobile notification
        mail_user_ids = NotificationSetting.get_user_mail(category_id=NOTIFY_SHARING, user_ids=[primary_owner.user_id])
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=[primary_owner.user_id]
        )

        if member_status == PM_MEMBER_STATUS_ACCEPTED:
            fcm_event = FCM_TYPE_CONFIRM_SHARE
        elif member_status == PM_MEMBER_STATUS_CONFIRMED:
            fcm_event = FCM_TYPE_ACCEPT_SHARE
        else:
            fcm_event = FCM_TYPE_REJECT_SHARE
        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        fcm_message = FCMRequestEntity(
            fcm_ids=list(fcm_ids), priority="high",
            data={
                "event": fcm_event,
                "data": {
                    "id": sharing_invitation.team_id,
                    "share_type": shared_type_name,
                    "pwd_user_ids": [primary_owner.user_id],
                    "name": request.data.get("user_fullname"),
                    "recipient_name": request.data.get("user_fullname"),
                }
            }
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})
        return Response(status=200, data={
            "status": status,
            "owner": primary_owner.user_id,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids,
            "member_status": member_status,
            "share_type": shared_type_name,
            "item_id": item_id,
            "folder_id": folder_id,
            "cipher_id": cipher_id
        })

    @action(methods=["put"], detail=False)
    def share(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)
        self.allow_personal_sharing(user=user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        sharing_key = validated_data.get("sharing_key")
        members = validated_data.get("members")
        groups = validated_data.get("groups") or []
        cipher = validated_data.get("cipher")
        shared_cipher_data = validated_data.get("shared_cipher_data")
        folder = validated_data.get("folder")

        shared_type_name = None
        cipher_id = None
        folder_id = None
        try:
            share_result = self.share_cipher_or_folder(
                sharing_key=sharing_key, members=members, groups=groups,
                cipher=cipher, shared_cipher_data=shared_cipher_data, folder=folder
            )
        except ValidationError as e:
            raise e

        new_sharing = share_result.get("new_sharing")
        existed_member_users = share_result.get("existed_member_users")
        non_existed_member_users = share_result.get("non_existed_member_users")

        PwdSync(event=SYNC_EVENT_MEMBER_INVITATION, user_ids=existed_member_users + [user.user_id]).send()
        if cipher:
            cipher_obj = new_sharing.ciphers.first()
            if cipher_obj:
                shared_type_name = cipher_obj.type
                cipher_id = cipher_obj.id
                delete_sync_cache_data(user_id=user.user_id)
                PwdSync(
                    event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id], team=new_sharing, add_all=True
                ).send(data={"id": cipher_obj.id})
        if folder:
            shared_type_name = "folder"
            share_collection = new_sharing.collections.first()
            folder_id = share_collection.id if share_collection else None
            delete_sync_cache_data(user_id=user.user_id)
            PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id], team=new_sharing, add_all=True).send()

        mail_user_ids = NotificationSetting.get_user_mail(category_id=NOTIFY_SHARING, user_ids=existed_member_users)
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )

        # Push mobile notification
        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        fcm_message = FCMRequestEntity(
            fcm_ids=fcm_ids, priority="high",
            data={
                "event": FCM_TYPE_NEW_SHARE,
                "data": {
                    "pwd_user_ids": notification_user_ids,
                    "share_type": shared_type_name,
                    "owner_name": request.data.get("owner_name")
                }
            }
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})

        # Update activity logs:
        user_enterprise_ids = list(Enterprise.objects.filter(
            enterprise_members__user=user, enterprise_members__status=E_MEMBER_STATUS_CONFIRMED
        ).values_list('id', flat=True))
        if user_enterprise_ids:
            ip = request.data.get("ip")
            emails = [m.get("email") for m in members]
            item_type = MAP_CIPHER_TYPE_STR.get(shared_type_name) if shared_type_name != 'folder' else shared_type_name
            LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id, "acting_user_id": user.user_id,
                "type": EVENT_ITEM_SHARE_CREATED, "ip_address": ip, "cipher_id": cipher_id, "collection_id": folder_id,
                "metadata": {"item_type": item_type, "emails": emails}
            })

        return Response(status=200, data={
            "id": str(new_sharing.id),
            "shared_type_name": shared_type_name,
            "folder_id": folder_id,
            "cipher_id": cipher_id,
            "non_existed_member_users": non_existed_member_users,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids,
        })

    @action(methods=["put"], detail=False)
    def multiple_share(self, request, *args, **kwargs):
        ip = request.data.get("ip")
        user = self.request.user
        self.check_pwd_session_auth(request)
        self.allow_personal_sharing(user=user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        sharing_key = validated_data.get("sharing_key")
        ciphers = validated_data.get("ciphers")
        folders = validated_data.get("folders")

        existed_member_users = []
        non_existed_member_users = []
        user_enterprise_ids = list(Enterprise.objects.filter(
            enterprise_members__user=user, enterprise_members__status=E_MEMBER_STATUS_CONFIRMED
        ).values_list('id', flat=True))

        if ciphers:
            for cipher_member in ciphers:
                try:
                    members = cipher_member.get("members") or []
                    cipher = cipher_member.get("cipher")
                    share_result = self.share_cipher_or_folder(
                        sharing_key=sharing_key,
                        members=members,
                        groups=cipher_member.get("groups") or [],
                        cipher=cipher,
                        shared_cipher_data=cipher_member.get("shared_cipher_data"), folder=None
                    )
                    # Create activity logs
                    if user_enterprise_ids:
                        emails = [m.get("email") for m in members]
                        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(
                            func_name="create_by_enterprise_ids", **{
                                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id,
                                "acting_user_id": user.user_id,
                                "type": EVENT_ITEM_SHARE_CREATED, "ip_address": ip,
                                "cipher_id": cipher.get("id"),
                                "metadata": {
                                    "item_type": MAP_CIPHER_TYPE_STR.get(cipher.get("type")),
                                    "emails": emails
                                }
                            })
                except ValidationError:
                    continue
                existed_member_users += share_result.get("existed_member_users", [])
                non_existed_member_users += share_result.get("non_existed_member_users", [])

        if folders:
            for folder in folders:
                try:
                    members = folder.get("members") or []
                    share_result = self.share_cipher_or_folder(
                        sharing_key=sharing_key,
                        members=members,
                        groups=folder.get("groups") or [],
                        cipher=None, shared_cipher_data=None, folder=folder
                    )
                    # Create activity logs
                    if user_enterprise_ids:
                        emails = [m.get("email") for m in members]
                        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(
                            func_name="create_by_enterprise_ids", **{
                                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id,
                                "acting_user_id": user.user_id,
                                "type": EVENT_ITEM_SHARE_CREATED, "ip_address": ip,
                                "metadata": {"item_type": "folder", "emails": emails}
                            })
                except ValidationError as e:
                    # raise e
                    continue
                existed_member_users += share_result.get("existed_member_users", [])
                non_existed_member_users += share_result.get("non_existed_member_users", [])

        # Sync the invitation
        share_type = "folder" if folders else "cipher"
        sync_user_ids = existed_member_users + [user.user_id]
        # Sync member invitation
        PwdSync(event=SYNC_EVENT_MEMBER_INVITATION, user_ids=sync_user_ids).send()
        # Sync ciphers
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=sync_user_ids).send()

        # Get notification user: Mail and notification
        mail_user_ids = NotificationSetting.get_user_mail(category_id=NOTIFY_SHARING, user_ids=existed_member_users)
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )

        # Send mobile notification
        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        fcm_message = FCMRequestEntity(
            fcm_ids=fcm_ids, priority="high",
            data={
                "event": FCM_TYPE_NEW_SHARE,
                "data": {
                    "pwd_user_ids": notification_user_ids,
                    "count": len(ciphers),
                    "owner_name": request.data.get("owner_name")
                }
            }
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})

        return Response(status=200, data={
            "shared_type_name": share_type,
            "non_existed_member_users": non_existed_member_users,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids,
        })

    def share_cipher_or_folder(self, sharing_key, members, groups, cipher, shared_cipher_data, folder):
        user = self.request.user
        cipher_obj = None
        folder_obj = None
        folder_name = None
        folder_ciphers = None

        # Validate the cipher
        if cipher:
            try:
                cipher_obj = self.cipher_repository.get_by_id(cipher_id=cipher.get("id"))
            except ObjectDoesNotExist:
                raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
            # If the cipher isn't shared?
            if cipher_obj.user and cipher_obj.user != user:
                raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
            # If the cipher obj belongs to a team
            if cipher_obj.team:
                # Check the team is a personal sharing team?
                if cipher_obj.team.personal_share is False:
                    raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
                # Check the user is an owner?
                if cipher_obj.team.team_members.filter(user=user, role_id=MEMBER_ROLE_OWNER).exists() is False:
                    raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
                # Check the team only shares this cipher?
                if cipher_obj.team.collections.exists() is True:
                    raise ValidationError(detail={"cipher": ["The cipher belongs to a collection"]})
            shared_cipher_data = json.loads(json.dumps(shared_cipher_data))

        if folder:
            folder_id = folder.get("id")
            folder_name = folder.get("name")
            folder_ciphers = folder.get("ciphers") or []
            try:
                folder_obj = self.folder_repository.get_by_id(folder_id=folder_id, user=user)
            except ObjectDoesNotExist:
                raise ValidationError(detail={"folder": ["The folder does not exist"]})
            # Check the list folder_ciphers in the folder
            folder_ciphers_obj = user.ciphers.filter(
                Q(folders__icontains="{}: '{}'".format(user.user_id, folder_id)) |
                Q(folders__icontains='{}: "{}"'.format(user.user_id, folder_id))
            ).values_list('id', flat=True)
            for folder_cipher in folder_ciphers:
                if folder_cipher.get("id") not in list(folder_ciphers_obj):
                    raise ValidationError({"non_field_errors": [gen_error("5000")]})
            folder_ciphers = json.loads(json.dumps(folder_ciphers))

        new_sharing, existed_member_users, non_existed_member_users = self.sharing_repository.create_new_sharing(
            sharing_key=sharing_key, members=members, groups=groups,
            cipher=cipher_obj, shared_cipher_data=shared_cipher_data,
            folder=folder_obj, shared_collection_name=folder_name, shared_collection_ciphers=folder_ciphers
        )

        return {
            "new_sharing": new_sharing,
            "existed_member_users": existed_member_users,
            "non_existed_member_users": non_existed_member_users,
            "cipher_obj": cipher_obj,
            "folder_obj": folder_obj
        }

    @action(methods=["post"], detail=False)
    def invitation_confirm(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(kwargs.get("pk"))
        member_id = kwargs.get("member_id")
        key = request.data.get("key")
        if not key:
            raise ValidationError(detail={"key": ["This field is required"]})
        # Retrieve member that accepted
        try:
            member = personal_share.team_members.get(id=member_id, status=PM_MEMBER_STATUS_ACCEPTED)
        except ObjectDoesNotExist:
            raise NotFound
        self.sharing_repository.confirm_invitation(member=member, key=key)
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[member.user_id]).send()
        PwdSync(event=SYNC_EVENT_MEMBER_CONFIRMED, user_ids=[member.user_id, user.user_id]).send()

        # Sending notification
        shared_type_name = None
        item_id = None
        cipher_id = None
        folder_id = None
        if member.team.collections.exists() is False:
            share_cipher = member.team.ciphers.first()
            if share_cipher:
                shared_type_name = share_cipher.type
                item_id = share_cipher.id
                cipher_id = item_id
        # Else, share a folder
        else:
            share_collection = member.team.collections.first()
            if share_collection:
                shared_type_name = "folder"
                item_id = share_collection.id
                folder_id = item_id
        mail_user_ids = NotificationSetting.get_user_mail(category_id=NOTIFY_SHARING, user_ids=[member.user_id])
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=[member.user_id]
        )
        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        fcm_message = FCMRequestEntity(
            fcm_ids=list(fcm_ids), priority="high",
            data={
                "event": FCM_TYPE_NEW_SHARE_AFTER_OWNER_CONFIRMED,
                "data": {
                    "id": member.team_id,
                    "share_type": shared_type_name,
                    "pwd_user_ids": [member.user_id],
                    # "name": request.data.get("user_fullname"),
                    # "recipient_name": request.data.get("user_fullname"),
                }
            }
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})

        return Response(status=200, data={
            "success": True,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids,
            "share_type": shared_type_name,
            "item_id": item_id,
            "folder_id": folder_id,
            "cipher_id": cipher_id
        })

    @action(methods=["put"], detail=False)
    def update_role(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(sharing_id=kwargs.get("pk"))
        member_id = kwargs.get("member_id")
        # Retrieve member that accepted
        try:
            member = personal_share.team_members.get(id=member_id)
        except ObjectDoesNotExist:
            raise NotFound
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        role = validated_data.get("role")
        hide_passwords = validated_data.get("hide_passwords", member.hide_passwords)

        self.sharing_repository.update_role_invitation(
            member=member, role_id=role, hide_passwords=hide_passwords
        )
        # If share a cipher:
        primary_member = self.team_repository.get_primary_member(team=member.team)
        PwdSync(event=SYNC_EVENT_MEMBER_UPDATE, user_ids=[member.user_id, primary_member.user_id]).send()
        if member.team.collections.all().exists() is False:
            share_cipher = member.team.ciphers.first()
            PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[member.user_id]).send(data={"id": share_cipher.id})
        # Else, share a folder
        else:
            share_collection = member.team.collections.first()
            PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[member.user_id]).send(
                data={"id": share_collection.id}
            )

        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def invitation_group_confirm(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(sharing_id=kwargs.get("pk"))
        group_id = kwargs.get("group_id")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        members_data = serializer.validated_data.get("members") or []
        # Retrieve member that accepted
        try:
            group = personal_share.groups.get(enterprise_group_id=group_id)
        except ObjectDoesNotExist:
            raise NotFound
        members_user_ids = [member_data.get("user_id") for member_data in members_data if member_data.get("user_id")]
        invited_members = group.groups_members.filter(
            member__status__in=[PM_MEMBER_STATUS_ACCEPTED, PM_MEMBER_STATUS_INVITED],
            member__user_id__in=members_user_ids
        ).select_related('member')
        for invited_member in invited_members:
            member_data = next(
                (item for item in members_data if item["user_id"] == invited_member.member.user_id), None
            )
            if member_data and member_data.get("key"):
                self.sharing_repository.confirm_invitation(member=invited_member.member, key=member_data.get("key"))
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=members_user_ids).send()
        PwdSync(event=SYNC_EVENT_MEMBER_CONFIRMED, user_ids=members_user_ids + [user.user_id]).send()
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def update_group_role(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(sharing_id=kwargs.get("pk"))
        group_id = kwargs.get("group_id")
        # Retrieve member that accepted
        try:
            group = personal_share.groups.get(enterprise_group_id=group_id)
        except ObjectDoesNotExist:
            raise NotFound

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        role = validated_data.get("role")
        group = self.sharing_repository.update_group_role_invitation(group=group, role_id=role)
        # If share a cipher:
        primary_member = self.team_repository.get_primary_member(team=group.team)
        group_members_user_ids = list(group.groups_members.values_list('member__user_id', flat=True))
        PwdSync(event=SYNC_EVENT_MEMBER_UPDATE, user_ids=group_members_user_ids + [primary_member.user_id]).send()
        if group.team.collections.all().exists() is False:
            share_cipher = group.team.ciphers.first()
            PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=group_members_user_ids).send(data={"id": share_cipher.id})
        # Else, share a folder
        else:
            share_collection = group.team.collections.first()
            PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=group_members_user_ids).send(
                data={"id": share_collection.id}
            )

        return Response(status=200, data={"success": True})

    @action(methods=["get"], detail=False)
    def my_share(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        user = request.user

        my_shared_teams = []
        personal_shared_teams = self.sharing_repository.get_my_personal_shared_teams(user=user).annotate(
            collection_count=Count('collections')
        )

        type_param = self.request.query_params.get("type")
        if type_param == "item":
            personal_shared_teams = personal_shared_teams.exclude(collection_count__gte=1)
        elif type_param == "folder":
            personal_shared_teams = personal_shared_teams.filter(collection_count__gte=1)

        for personal_shared_team in personal_shared_teams:
            shared_members = self.sharing_repository.get_shared_members(
                personal_shared_team=personal_shared_team, exclude_owner=True, is_added_by_group=False
            )
            shared_members_data = []
            for member in shared_members:
                shared_members_data.append({
                    "id": member.id,
                    "access_time": member.access_time,
                    "user_id": member.user_id,
                    "email": member.email,
                    "role": member.role_id,
                    "status": member.status,
                    "hide_passwords": member.hide_passwords,
                    "share_type": self.sharing_repository.get_personal_share_type(member=member),
                    "pwd_user_id": member.user.internal_id if member.user else None
                })

            shared_groups = self.sharing_repository.get_shared_groups(personal_share_team=personal_shared_team)
            shared_groups_data = []
            for group in shared_groups:
                shared_groups_data.append({
                    "id": group.enterprise_group_id,
                    "name": group.name,
                    "access_time": group.creation_date,
                    "role": group.role_id,
                    "share_type": self.sharing_repository.get_share_type(role_id=group.role_id),
                })

            team_data = {
                "id": personal_shared_team.id,
                "name": personal_shared_team.name,
                "description": personal_shared_team.description,
                "organization_id": personal_shared_team.id,
                "members": shared_members_data,
                "groups": shared_groups_data
            }
            my_shared_teams.append(team_data)
        return Response(status=200, data=my_shared_teams)

    @action(methods=["post"], detail=False)
    def stop_share(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(kwargs.get("pk"))
        member_id = kwargs.get("member_id")
        group_id = kwargs.get("group_id")

        group = None
        if group_id:
            try:
                group = personal_share.groups.get(enterprise_group_id=group_id)
            except ObjectDoesNotExist:
                raise NotFound
        member = None
        if member_id:
            try:
                member = personal_share.team_members.exclude(user=user).get(id=member_id)
            except ObjectDoesNotExist:
                raise NotFound
        shared_team = group.team if group else member.team

        # Check plan of the user
        self.allow_personal_sharing(user=user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        cipher = validated_data.get("cipher")
        personal_cipher_data = validated_data.get("personal_cipher_data")
        folder = validated_data.get("folder")
        cipher_obj = None
        collection_obj = None
        folder_name = None
        folder_ciphers = None

        if cipher:
            cipher_id = cipher.get("id")
            try:
                cipher_obj = self.cipher_repository.get_by_id(cipher_id)
                if cipher_obj.team != shared_team:
                    raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
            except ObjectDoesNotExist:
                raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
            personal_cipher_data = json.loads(json.dumps(personal_cipher_data))

        if folder:
            folder_id = folder.get("id")
            folder_name = folder.get("name")
            folder_ciphers = folder.get("ciphers") or []
            # Get collection of the team
            try:
                collection_obj = self.collection_repository.get_team_collection_by_id(
                    collection_id=folder_id, team_id=shared_team.id
                )
            except ObjectDoesNotExist:
                raise ValidationError(detail={"folder": ["The folder does not exist"]})
            # Check the list folder_ciphers in the folder
            collection_ciphers_obj = collection_obj.collections_ciphers.values_list('cipher_id', flat=True)
            if collection_ciphers_obj and not folder_ciphers:
                raise ValidationError(detail={"folder": ["The ciphers is not allow empty"]})
            for folder_cipher in folder_ciphers:
                if folder_cipher.get("id") not in list(collection_ciphers_obj):
                    raise ValidationError(detail={"folder": [
                        "The collection does not have the cipher {}".format(folder_cipher.get("id"))
                    ]})
            folder_ciphers = json.loads(json.dumps(folder_ciphers))

        removed_member_user_ids = self.sharing_repository.stop_share(
            member=member, group=group,
            cipher=cipher_obj, cipher_data=personal_cipher_data,
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )
        PwdSync(event=SYNC_EVENT_MEMBER_REMOVE, user_ids=[user.user_id] + removed_member_user_ids).send()
        # Re-sync data of the owner and removed member
        if cipher_obj:
            PwdSync(
                event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id] + removed_member_user_ids
            ).send(data={"id": cipher_obj.id})
        if collection_obj:
            PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id] + removed_member_user_ids).send()

        # Delete cached data
        for u_id in [user.user_id] + removed_member_user_ids:
            delete_sync_cache_data(user_id=u_id)

        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def leave(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(kwargs.get("pk"))
        # Retrieve member that accepted
        try:
            member = personal_share.team_members.exclude(role_id=MEMBER_ROLE_OWNER).get(user=user)
            team = member.team
        except ObjectDoesNotExist:
            raise NotFound
        member_user_id = self.sharing_repository.leave_share(member=member)

        # Re-sync data of the member
        # If share a cipher
        if team.collections.all().exists() is False:
            share_cipher = team.ciphers.first()
            delete_sync_cache_data(user_id=member_user_id)
            PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[member_user_id]).send(data={"id": share_cipher.id})
        # Else, share a folder
        else:
            share_collection = team.collections.first()
            delete_sync_cache_data(user_id=user.user_id)
            PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[user.user_id]).send(data={"id": share_collection.id})

        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def stop_share_cipher_folder(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(sharing_id=kwargs.get("pk"))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        cipher = validated_data.get("cipher")
        personal_cipher_data = validated_data.get("personal_cipher_data")
        folder = validated_data.get("folder")
        cipher_obj = None
        collection_obj = None
        folder_name = None
        folder_ciphers = None

        if cipher:
            cipher_id = cipher.get("id")
            try:
                cipher_obj = self.cipher_repository.get_by_id(cipher_id)
                if cipher_obj.team != personal_share:
                    raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
            except ObjectDoesNotExist:
                raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
            personal_cipher_data = json.loads(json.dumps(personal_cipher_data))
        if folder:
            folder_id = folder.get("id")
            folder_name = folder.get("name")
            folder_ciphers = folder.get("ciphers") or []
            # Get collection of the team
            try:
                collection_obj = self.collection_repository.get_team_collection_by_id(
                    collection_id=folder_id, team_id=personal_share.id
                )
            except ObjectDoesNotExist:
                raise ValidationError(detail={"folder": ["The folder does not exist"]})
            # Check the list folder_ciphers in the folder
            collection_ciphers_obj = collection_obj.collections_ciphers.values_list('cipher_id', flat=True)
            if collection_ciphers_obj and not folder_ciphers:
                raise ValidationError(detail={"folder": ["The ciphers is not allow empty"]})
            for folder_cipher in folder_ciphers:
                if folder_cipher.get("id") not in list(collection_ciphers_obj):
                    raise ValidationError(detail={"folder": [
                        "The collection does not have the cipher {}".format(folder_cipher.get("id"))
                    ]})
            folder_ciphers = json.loads(json.dumps(folder_ciphers))

        removed_members_user_id, personal_folder_id = self.sharing_repository.stop_share_all_members(
            team=personal_share,
            cipher=cipher_obj, cipher_data=personal_cipher_data,
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )
        PwdSync(event=SYNC_EVENT_MEMBER_REMOVE, user_ids=[user.user_id] + removed_members_user_id).send()
        # Re-sync data of the owner and removed member
        if cipher_obj:
            PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id] + removed_members_user_id).send(
                data={"id": cipher_obj.id}
            )
        if collection_obj:
            PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id] + removed_members_user_id).send()

        return Response(status=200, data={"success": True, "personal_folder_id": personal_folder_id})

    @action(methods=["post"], detail=False)
    def add_member(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(kwargs.get("pk"))
        share_folder = personal_share.collections.first()
        if not share_folder:
            raise NotFound
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        members = validated_data.get("members")
        groups = validated_data.get("groups")

        existed_member_users, non_existed_member_users = self.sharing_repository.add_members(
            team=personal_share, shared_collection=share_folder, members=members, groups=groups
        )
        PwdSync(event=SYNC_EVENT_MEMBER_INVITATION, user_ids=existed_member_users + [user.user_id]).send()
        mail_user_ids = NotificationSetting.get_user_mail(category_id=NOTIFY_SHARING, user_ids=existed_member_users)
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )
        return Response(status=200, data={
            "id": personal_share.id,
            "shared_type_name": "folder",
            "non_existed_member_users": non_existed_member_users,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["put"], detail=False)
    def update_share_folder(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(kwargs.get("pk"))
        # Retrieve collection
        try:
            collection = personal_share.collections.get(id=kwargs.get("folder_id"))
        except ObjectDoesNotExist:
            raise NotFound
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        name = validated_data.get("name")
        collection = self.collection_repository.save_update_collection(collection=collection, name=name)
        delete_sync_cache_data(user_id=user.user_id)
        PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[user.user_id], team=personal_share, add_all=True).send(
            data={"id": collection.id}
        )
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
        #     "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_COLLECTION_UPDATED, "collection_id": collection.id, "ip_address": ip
        # })
        return Response(status=200, data={"id": collection.id})

    @action(methods=["post"], detail=False)
    def delete_share_folder(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(sharing_id=kwargs.get("pk"))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        folder = validated_data.get("folder")
        folder_id = folder.get("id")
        folder_name = folder.get("name")
        folder_ciphers = folder.get("ciphers") or []

        # Get collection of the team
        try:
            collection_obj = self.collection_repository.get_team_collection_by_id(
                collection_id=folder_id, team_id=personal_share.id
            )
        except ObjectDoesNotExist:
            raise ValidationError(detail={"folder": ["The folder does not exist"]})
        # Check the list folder_ciphers in the folder
        collection_ciphers_obj = collection_obj.collections_ciphers.values_list('cipher_id', flat=True)
        for folder_cipher in folder_ciphers:
            if folder_cipher.get("id") not in list(collection_ciphers_obj):
                raise ValidationError(detail={"folder": [
                    "The collection does not have the cipher {}".format(folder_cipher.get("id"))
                ]})
        folder_ciphers = json.loads(json.dumps(folder_ciphers))

        removed_members_user_id = self.sharing_repository.delete_share_folder(
            team=personal_share,
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )
        PwdSync(event=SYNC_EVENT_MEMBER_REMOVE, user_ids=[user.user_id] + removed_members_user_id).send()
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id] + removed_members_user_id).send()
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def stop_share_folder(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(sharing_id=kwargs.get("pk"))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        folder = validated_data.get("folder")
        folder_id = folder.get("id")
        folder_name = folder.get("name")
        folder_ciphers = folder.get("ciphers") or []
        # Get collection of the team
        try:
            collection_obj = self.collection_repository.get_team_collection_by_id(
                collection_id=folder_id, team_id=personal_share.id
            )
        except ObjectDoesNotExist:
            raise ValidationError(detail={"folder": ["The folder does not exist"]})
        # Check the list folder_ciphers in the folder
        collection_ciphers_obj = collection_obj.collections_ciphers.values_list('cipher_id', flat=True)
        if collection_ciphers_obj and not folder_ciphers:
            raise ValidationError(detail={"folder": ["The ciphers is not allow empty"]})
        for folder_cipher in folder_ciphers:
            if folder_cipher.get("id") not in list(collection_ciphers_obj):
                raise ValidationError(detail={"folder": [
                    "The collection does not have the cipher {}".format(folder_cipher.get("id"))
                ]})
        folder_ciphers = json.loads(json.dumps(folder_ciphers))

        removed_members_user_id, personal_folder_id = self.sharing_repository.stop_share_all_members(
            team=personal_share,
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )
        PwdSync(event=SYNC_EVENT_MEMBER_REMOVE, user_ids=[user.user_id] + removed_members_user_id).send()
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id] + removed_members_user_id).send()
        return Response(status=200, data={"success": True, "personal_folder_id": personal_folder_id})

    @action(methods=["post"], detail=False)
    def add_item_share_folder(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(sharing_id=kwargs.get("pk"))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        cipher_data = validated_data.get("cipher")
        # Get collection of the team
        try:
            collection_obj = self.collection_repository.get_team_collection_by_id(
                collection_id=kwargs.get("folder_id"), team_id=personal_share.id
            )
        except ObjectDoesNotExist:
            raise ValidationError(detail={"folder": ["The folder does not exist"]})

        try:
            cipher_obj = self.cipher_repository.get_by_id(cipher_id=cipher_data.get("id"))
            if cipher_obj.team_id:
                raise ValidationError({"non_field_errors": [gen_error("5000")]})
            if cipher_obj.user != user:
                raise ValidationError(detail={"cipher": {"id": ["The cipher id does not exist"]}})
        except ObjectDoesNotExist:
            raise ValidationError(detail={"cipher": {"id": ["The cipher id does not exist"]}})

        cipher_data["team_id"] = personal_share.id
        cipher_data["collection_ids"] = [collection_obj.id]
        cipher_data["user_id"] = user.user_id
        cipher_data = json.loads(json.dumps(cipher_data))
        cipher = self.cipher_repository.save_share_cipher(cipher=cipher_obj, cipher_data=cipher_data)
        collection_obj.revision_date = now()
        collection_obj.save()
        delete_sync_cache_data(user_id=user.user_id)
        PwdSync(
            event=SYNC_EVENT_CIPHER_UPDATE,
            user_ids=[user.user_id],
            team=personal_share,
            add_all=True
        ).send(data={"id": cipher.id})

        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def remove_item_share_folder(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(sharing_id=kwargs.get("pk"))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        cipher_data = validated_data.get("cipher")
        # Get collection of the team
        try:
            collection_obj = self.collection_repository.get_team_collection_by_id(
                collection_id=kwargs.get("folder_id"), team_id=personal_share.id
            )
        except ObjectDoesNotExist:
            raise ValidationError(detail={"folder": ["The folder does not exist"]})

        try:
            cipher_obj = self.cipher_repository.get_by_id(cipher_id=cipher_data.get("id"))
            if cipher_obj.team_id != personal_share.id:
                raise ValidationError(detail={"cipher": {"id": ["The cipher id does not exist"]}})
        except ObjectDoesNotExist:
            raise ValidationError(detail={"cipher": {"id": ["The cipher id does not exist"]}})

        cipher_data["team_id"] = None
        cipher_data["collection_ids"] = []
        cipher_data["user_id"] = user.user_id
        cipher_data = json.loads(json.dumps(cipher_data))
        cipher = self.cipher_repository.save_share_cipher(cipher=cipher_obj, cipher_data=cipher_data)
        collection_obj.revision_date = now()
        collection_obj.save()
        delete_sync_cache_data(user_id=user.user_id)
        PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id], team=personal_share, add_all=True).send(
            data={"id": cipher.id}
        )

        return Response(status=200, data={"success": True})