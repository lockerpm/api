import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.background import BG_EVENT, LockerBackgroundFactory
from shared.constants.event import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.sharing_pwd_permission import SharingPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_VAULT
from v1_0.sharing.serializers import UserPublicKeySerializer, SharingSerializer
from v1_0.apps import PasswordManagerViewSet


class SharingPwdViewSet(PasswordManagerViewSet):
    permission_classes = (SharingPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "public_key":
            self.serializer_class = UserPublicKeySerializer
        elif self.action == "share":
            self.serializer_class = SharingSerializer
        return super(SharingPwdViewSet, self).get_serializer_class()

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
        validated_data = serializer.validated_data
        sharing_key = validated_data.get("sharing_key")
        members = validated_data.get("members")
        cipher = validated_data.get("cipher")
        folder = validated_data.get("folder")


