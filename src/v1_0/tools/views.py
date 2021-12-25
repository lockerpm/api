from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from core.utils.data_helpers import camel_snake_data
from shared.constants.transactions import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.tool_pwd_permission import ToolPwdPermission
from shared.services.hibp.hibp_service import HibpService
from v1_0.tools.serializers import BreachSerializer
from v1_0.apps import PasswordManagerViewSet


class ToolPwdViewSet(PasswordManagerViewSet):
    permission_classes = (ToolPwdPermission, )

    def get_serializer_class(self):
        if self.action == "breach":
            self.serializer_class = BreachSerializer
        return super(ToolPwdViewSet, self).get_serializer_class()

    def get_object(self):
        user = self.request.user
        # Only premium plan
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        plan_obj = current_plan.get_plan_obj()

        if self.action == "breach":
            if plan_obj.allow_tools_data_breach() is False:
                raise ValidationError({"non_field_errors": [gen_error("7002")]})

        return user

    @action(methods=["post"], detail=False)
    def breach(self, request, *args, **kwargs):
        self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        # Request to https://haveibeenpwned.com/api/v3/breachedaccount
        hibp_check = HibpService().check_breach(email=email)
        if not hibp_check:
            return Response(status=200, data=[])
        hibp_check = camel_snake_data(hibp_check, camel_to_snake=True)
        return Response(status=200, data=hibp_check)
