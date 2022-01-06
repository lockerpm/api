import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.sharing_pwd_permission import SharingPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_VAULT, SYNC_EVENT_MEMBER_ACCEPTED, \
    SYNC_EVENT_CIPHER
from v1_0.sharing.serializers import UserPublicKeySerializer, SharingSerializer, SharingInvitationSerializer, \
    StopSharingSerializer, UpdateInvitationRoleSerializer
from v1_0.apps import PasswordManagerViewSet


class SharingPwdViewSet(PasswordManagerViewSet):
    permission_classes = (SharingPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "public_key":
            self.serializer_class = UserPublicKeySerializer
        elif self.action == "share":
            self.serializer_class = SharingSerializer
        elif self.action == "invitations":
            self.serializer_class = SharingInvitationSerializer
        elif self.action == "stop_share":
            self.serializer_class = StopSharingSerializer
        elif self.action == "update_role":
            self.serializer_class = UpdateInvitationRoleSerializer
        return super(SharingPwdViewSet, self).get_serializer_class()

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
                raise ValidationError(detail={"user_id": ["The user does not exist"]})
        except ObjectDoesNotExist:
            raise ValidationError(detail={"user_id": ["The user does not exist"]})
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
        if status == "accept":
            self.sharing_repository.accept_invitation(member=sharing_invitation)
            primary_owner = self.team_repository.get_primary_member(team=sharing_invitation.team)
            PwdSync(event=SYNC_EVENT_MEMBER_ACCEPTED, user_ids=[primary_owner.user_id, user.user_id]).send()
            result = {"status": status, "owner": primary_owner.user_id, "team_name": sharing_invitation.team.name}
        else:
            self.sharing_repository.reject_invitation(member=sharing_invitation)
            result = {"status": status}
        return Response(status=200, data=result)

    @action(methods=["put"], detail=False)
    def share(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)

        # Check plan of the user
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        plan_obj = current_plan.get_plan_obj()
        if plan_obj.allow_personal_share() is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        sharing_key = validated_data.get("sharing_key")
        members = validated_data.get("members")
        cipher = validated_data.get("cipher")
        shared_cipher_data = validated_data.get("shared_cipher_data")
        folder = validated_data.get("folder")
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
                    raise ValidationError(detail={"folder": [
                        "The folder does not have the cipher {}".format(folder_cipher.get("id"))
                    ]})
            folder_ciphers = json.loads(json.dumps(folder_ciphers))

        new_sharing, existed_member_users, non_existed_member_users = self.sharing_repository.create_new_sharing(
            sharing_key=sharing_key, members=members,
            cipher=cipher_obj, shared_cipher_data=shared_cipher_data,
            folder=folder_obj, shared_collection_name=folder_name, shared_collection_ciphers=folder_ciphers
        )
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[request.user.user_id], team=new_sharing, add_all=True).send()

        return Response(status=200, data={"id": new_sharing.id})

    @action(methods=["post"], detail=False)
    def invitation_confirm(self, request, *args, **kwargs):
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
        return Response(status=200, data={"success": True})

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
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[member.user_id]).send()

        return Response(status=200, data={"success": True})

    @action(methods=["get"], detail=False)
    def my_share(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        user = request.user

        my_shared_teams = []
        personal_shared_teams = self.sharing_repository.get_my_personal_shared_teams(user=user)
        for personal_shared_team in personal_shared_teams:
            shared_members = self.sharing_repository.get_shared_members(
                personal_shared_team=personal_shared_team, exclude_owner=True
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
            team_data = {
                "id": personal_shared_team.id,
                "name": personal_shared_team.name,
                "description": personal_shared_team.description,
                "organization_id": personal_shared_team.id,
                "members": shared_members_data
            }
            my_shared_teams.append(team_data)
        return Response(status=200, data=my_shared_teams)

    @action(methods=["post"], detail=False)
    def stop_share(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(kwargs.get("pk"))
        member_id = kwargs.get("member_id")
        # Retrieve member that accepted
        try:
            member = personal_share.team_members.exclude(user=user).get(id=member_id)
        except ObjectDoesNotExist:
            raise NotFound
        shared_team = member.team

        # Check plan of the user
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        plan_obj = current_plan.get_plan_obj()
        if plan_obj.allow_personal_share() is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})

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
            for folder_cipher in folder_ciphers:
                if folder_cipher.get("id") not in list(collection_ciphers_obj):
                    raise ValidationError(detail={"folder": [
                        "The collection does not have the cipher {}".format(folder_cipher.get("id"))
                    ]})
            folder_ciphers = json.loads(json.dumps(folder_ciphers))

        removed_member_user_id = self.sharing_repository.stop_share(
            member=member,
            cipher=cipher_obj, cipher_data=personal_cipher_data,
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )
        # Re-sync data of the owner and removed member
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id, removed_member_user_id]).send()
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def leave(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        personal_share = self.get_personal_share(kwargs.get("pk"))
        # Retrieve member that accepted
        try:
            member = personal_share.team_members.exclude(role_id=MEMBER_ROLE_OWNER).get(user=user)
        except ObjectDoesNotExist:
            raise NotFound

        member_user_id = self.sharing_repository.leave_share(member=member)
        # Re-sync data of the member
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[member_user_id]).send()
        return Response(status=200, data={"success": True})