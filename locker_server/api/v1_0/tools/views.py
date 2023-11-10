from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework import status

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.tool_pwd_permission import ToolPwdPermission
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.hibp.hibp_service import HibpService
from locker_server.shared.utils.app import camel_snake_data
from .serializers import BreachSerializer


class ToolPwdViewSet(APIBaseViewSet):
    permission_classes = (ToolPwdPermission,)

    def get_serializer_class(self):
        if self.action in ["breach", "public_breach"]:
            self.serializer_class = BreachSerializer
        return super().get_serializer_class()

    def get_object(self):
        user = self.request.user
        # Only premium plan
        current_plan = self.user_service.get_current_plan(user=user)
        plan_obj = current_plan.pm_plan

        if self.action == "breach":
            is_active_enterprise_member = self.user_service.is_active_enterprise_member(user_id=user.user_id)
            if is_active_enterprise_member is False and plan_obj.tools_data_breach is False:
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
        hibp_check = HibpService(retries_number=1).check_breach(email=email)
        if not hibp_check:
            return Response(status=status.HTTP_200_OK, data=[])
        hibp_check = camel_snake_data(hibp_check, camel_to_snake=True)
        return Response(status=status.HTTP_200_OK, data=hibp_check)

    @action(methods=["post"], detail=False)
    def public_breach(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        hibp_check = HibpService(retries_number=1).check_breach(email=email)
        if not hibp_check:
            return Response(status=status.HTTP_200_OK, data=[])
        hibp_check = camel_snake_data(hibp_check, camel_to_snake=True)
        return Response(status=status.HTTP_200_OK, data=hibp_check)
