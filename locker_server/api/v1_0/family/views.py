from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.family_pwd_permission import FamilyPwdPermission
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.exceptions.user_plan_exception import *
from locker_server.shared.constants.transactions import PLAN_TYPE_PM_FAMILY
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.external_services.user_notification.list_jobs import PWD_FAMILY_INVITATION, PWD_FAMILY_REMOVED
from .serializers import UserPlanFamilySerializer, CreateUserPlanFamilySerializer


class FamilyPwdViewSet(APIBaseViewSet):
    permission_classes = (FamilyPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "delete"]

    def get_serializer_class(self):
        if self.action == "member_list":
            self.serializer_class = UserPlanFamilySerializer
        elif self.action == "member_create":
            self.serializer_class = CreateUserPlanFamilySerializer
        return super().get_serializer_class()

    def get_object(self):
        user = self.request.user
        pm_current_plan = self.user_service.get_current_plan(user=user)
        # Check permission here
        if self.action == "member_list":
            if self.family_service.is_in_family_plan(user_plan=pm_current_plan) is False:
                raise PermissionDenied
        else:
            if not pm_current_plan.pm_plan.is_family_plan:
                raise PermissionDenied
        return pm_current_plan

    @action(methods=["get"], detail=False)
    def member_list(self, request, *args, **kwargs):
        self.get_object()
        family_members_owner = self.family_service.list_family_members(user_id=request.user.user_id)
        family_members = family_members_owner.get("family_members")
        owner = family_members_owner.get("owner")
        serializer = self.get_serializer(family_members, many=True)
        owner = [{
            "id": None,
            "created_time": owner.creation_date,
            "email": owner.email,
            "username": owner.username,
            "avatar": owner.get_avatar(),
            "full_name": owner.full_name,
        }]
        results = owner + serializer.data
        return Response(status=status.HTTP_200_OK, data=results)

    @action(methods=["post"], detail=False)
    def member_create(self, request, *args, **kwargs):
        pm_current_plan = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        emails = validated_data.get("family_members")

        family_members = []
        for member in emails:
            try:
                user_invited = self.user_service.retrieve_by_email(email=member)
                if not user_invited.activated:
                    continue
                family_members.append({
                    "user_id": user_invited.id,
                    "email": user_invited.email,
                    "name": user_invited.full_name,
                    "language": user_invited.language,
                })
            except UserDoesNotExistException:
                family_members.append({
                    "user_id": None,
                    "email": member,
                    "name": "there",
                    "language": "en"
                })
        try:
            self.family_service.create_multiple_family_members(
                user_id=pm_current_plan.user.user_id, family_members=family_members
            )
        except MaxUserPlanFamilyReachedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7012")]})
        except UserIsInOtherFamilyException as e:
            raise ValidationError(detail={
                "family_members": ["The user {} is in other family plan".format(e.email)]
            })
        if settings.SELF_HOSTED:
            for member in family_members:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_sending", **{
                        "destinations": [{
                            "email": member["email"], "language": member["language"], "name": member["name"]
                        }],
                        "job": PWD_FAMILY_INVITATION,
                        "owner_email": request.user.email,
                        "invited_email": member["email"],
                    }
                )
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["delete"], detail=False)
    def member_destroy(self, request, *args, **kwargs):
        member_id = kwargs.get("member_id")
        pm_current_plan = self.get_object()
        try:
            family_user_id, family_email = self.family_service.destroy_family_member(
                user_id=pm_current_plan.user.user_id, family_member_id=member_id
            )
        except UserPlanFamilyDoesNotExistException:
            raise NotFound

        if settings.SELF_HOSTED:
            if family_user_id:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_sending", **{
                        "user_ids": [family_user_id],
                        "job": PWD_FAMILY_REMOVED,
                    }
                )

            elif family_email:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_sending", **{
                        "destinations": [{
                            "email": family_email, "name": "there", "language": "en"
                        }],
                        "job": PWD_FAMILY_REMOVED,
                    }
                )

        return Response(status=200, data={"user_id": family_user_id, "email": family_email})
