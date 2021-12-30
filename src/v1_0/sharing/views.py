import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.background import BG_EVENT, LockerBackgroundFactory
from shared.constants.event import *
from shared.constants.members import PM_MEMBER_STATUS_INVITED, PM_MEMBER_STATUS_ACCEPTED
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.sharing_pwd_permission import SharingPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_VAULT, SYNC_EVENT_MEMBER_ACCEPTED, \
    SYNC_EVENT_CIPHER
from v1_0.sharing.serializers import UserPublicKeySerializer, SharingSerializer, SharingInvitationSerializer
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

        if cipher:
            cipher_id = cipher.get("id")
            try:
                cipher_obj = self.cipher_repository.get_by_id(cipher_id=cipher_id)
                if cipher_obj.user != user:
                    raise ValidationError(detail={"cipher": ["The cipher does not exist"]})
            except ObjectDoesNotExist:
                raise ValidationError(detail={"cipher": ["The cipher does not exist"]})

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

        new_sharing, existed_member_users, non_existed_member_users = self.sharing_repository.create_new_sharing(
            sharing_key=sharing_key, members=members,
            cipher=cipher_obj, shared_cipher_data=shared_cipher_data,
            folder=folder_obj, shared_collection_name=folder_name, shared_collection_ciphers=folder_ciphers
        )

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
