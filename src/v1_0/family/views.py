from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, FloatField, ExpressionWrapper, When, Q, Value, Case, IntegerField
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from core.utils.data_helpers import camel_snake_data
from core.utils.core_helpers import secure_random_string
from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.constants.members import PM_MEMBER_STATUS_INVITED, MEMBER_ROLE_OWNER, PM_MEMBER_STATUS_CONFIRMED, \
    MEMBER_ROLE_ADMIN, MEMBER_ROLE_MEMBER
from shared.constants.event import *
from shared.constants.transactions import *
from shared.error_responses.error import gen_error, refer_error
from shared.permissions.locker_permissions.family_pwd_permission import FamilyPwdPermission
from shared.permissions.locker_permissions.user_pwd_permission import UserPwdPermission
from shared.services.pm_sync import SYNC_EVENT_MEMBER_ACCEPTED, PwdSync, SYNC_EVENT_VAULT, SYNC_EVENT_MEMBER_UPDATE
from shared.utils.app import now
from shared.utils.network import detect_device
from v1_0.family.serializers import UserPlanFamilySerializer, CreateUserPlanFamilySeriaizer
from v1_0.apps import PasswordManagerViewSet


class FamilyPwdViewSet(PasswordManagerViewSet):
    permission_classes = (FamilyPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "delete"]

    def get_serializer_class(self):
        if self.action == "member_list":
            self.serializer_class = UserPlanFamilySerializer
        elif self.action == "member_create":
            self.serializer_class = CreateUserPlanFamilySeriaizer
        return super(FamilyPwdViewSet, self).get_serializer_class()

    def get_object(self):
        user = self.request.user
        pm_current_plan = self.user_repository.get_current_plan(user=user)
        current_plan_alias = pm_current_plan.get_plan_type_alias()
        # Check permission here
        if self.action == "member_list":
            if current_plan_alias != PLAN_TYPE_PM_FAMILY or user.pm_plan_family.exists() is False:
                raise PermissionDenied
        else:
            if current_plan_alias != PLAN_TYPE_PM_FAMILY:
                raise PermissionDenied
        return pm_current_plan

    @action(methods=["get"], detail=False)
    def member_list(self, request, *args, **kwargs):
        pm_current_plan = self.get_object()
        pm_current_plan_alias = pm_current_plan.get_plan_type_alias()
        # The retrieving user is owner of the family plan
        if pm_current_plan_alias == PLAN_TYPE_PM_FAMILY:
            family_members = pm_current_plan.pm_plan_family.all().order_by('-user_id', '-created_time')
        # Else, user is a member
        else:
            user = request.user
            family_user_plan = user.pm_plan_family.first()
            if family_user_plan:
                family_members = family_user_plan.root_user_plan.pm_plan_family.all().order_by(
                    '-user_id', '-created_time'
                )
            else:
                family_members = []
        serializer = self.get_serializer(family_members, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["post"], detail=False)
    def member_create(self, request, *args, **kwargs):
        pm_current_plan = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        family_members = validated_data.get("family_members")

        existed_family_members = pm_current_plan.pm_plan_family.all()
        pm_plan = pm_current_plan.get_plan_obj()
        if len(family_members) > pm_plan.get_max_number_members() - existed_family_members.count():
            raise ValidationError(detail={"family_members": [
                "The plan only accepts {} members including you".format(pm_plan.get_max_number_members())
            ]})

        for family_member in family_members:
            email = family_member.get("email")
            user_id = family_member.get("user_id")
            self.user_repository.add_to_family_sharing(
                family_user_plan=pm_current_plan, user_id=user_id, email=email
            )

        return Response(status=200, data={"success": True})

    @action(methods=["delete"], detail=False)
    def member_destroy(self, request, *args, **kwargs):
        user = self.request.user
        member_id = kwargs.get("member_id")
        pm_current_plan = self.get_object()
        try:
            family_member = pm_current_plan.pm_plan_family.get(id=member_id)
        except ObjectDoesNotExist:
            raise NotFound
        if family_member.user == user:
            raise PermissionDenied
        # Downgrade the plan of the member user
        if family_member.user:
            self.user_repository.update_plan(
                user=family_member.user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=settings.SCOPE_PWD_MANAGER
            )
        family_member.delete()
        return Response(status=204)
