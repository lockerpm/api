from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from shared.constants.transactions import PLAN_TYPE_PM_FREE
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.family_pwd_permission import FamilyPwdPermission
from v1_0.family.serializers import UserPlanFamilySerializer, CreateUserPlanFamilySeriaizer
from v1_0.general_view import PasswordManagerViewSet


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
        # Check permission here
        if self.action == "member_list":
            if not pm_current_plan.pm_plan.is_family_plan and user.pm_plan_family.exists() is False:
                raise PermissionDenied
        else:
            if not pm_current_plan.pm_plan.is_family_plan:
                raise PermissionDenied
        return pm_current_plan

    @action(methods=["get"], detail=False)
    def member_list(self, request, *args, **kwargs):
        pm_current_plan = self.get_object()
        # The retrieving user is owner of the family plan
        if pm_current_plan.pm_plan.is_family_plan:
            owner = request.user
            family_members = pm_current_plan.pm_plan_family.all().order_by('-user_id', '-created_time')
        # Else, user is a member
        else:
            user = request.user
            family_user_plan = user.pm_plan_family.first()
            owner = family_user_plan.root_user_plan.user
            if family_user_plan:
                family_members = family_user_plan.root_user_plan.pm_plan_family.all().order_by(
                    '-user_id', '-created_time'
                )
            else:
                family_members = []
        serializer = self.get_serializer(family_members, many=True)
        owner = [{"id": None, "user_id": owner.user_id, "created_time": owner.creation_date}]
        results = owner + serializer.data
        return Response(status=200, data=results)

    @action(methods=["post"], detail=False)
    def member_create(self, request, *args, **kwargs):
        pm_current_plan = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        family_members = validated_data.get("family_members")

        existed_family_members = pm_current_plan.pm_plan_family.all()
        pm_plan = pm_current_plan.get_plan_obj()

        if len(family_members) > pm_plan.get_max_number_members() - existed_family_members.count() - 1:
            raise ValidationError(detail={"non_field_errors": [gen_error("7012")]})

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
        family_user_id = family_member.user_id
        family_email = family_member.email
        family_member.delete()
        return Response(status=200, data={"user_id": family_user_id, "email": family_email})
