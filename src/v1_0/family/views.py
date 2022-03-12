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
from v1_0.family.serializers import UserPlanFamilySerializer
from v1_0.apps import PasswordManagerViewSet


class FamilyPwdViewSet(PasswordManagerViewSet):
    permission_classes = (FamilyPwdPermission, )
    http_method_names = ["head", "options", "get"]

    def get_serializer_class(self):
        if self.action == "member_list":
            self.serializer_class = UserPlanFamilySerializer
        return super(FamilyPwdViewSet, self).get_serializer_class()

    def get_object(self):
        user = self.request.user
        pm_current_plan = self.user_repository.get_current_plan(user=user)
        if pm_current_plan.get_plan_type_name() != PLAN_TYPE_PM_FAMILY:
            raise PermissionDenied
        return pm_current_plan

    @action(methods=["get"], detail=False)
    def member_list(self, request, *args, **kwargs):
        pm_current_plan = self.get_object()
        family_members = pm_current_plan.pm_plan_family.all().order_by('-user_id', '-created_time')
        serializer = self.get_serializer(family_members, many=True)
        return Response(status=200, data=serializer.data)

