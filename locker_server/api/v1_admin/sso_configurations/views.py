import json

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action

from locker_server.api.api_base_view import APIBaseViewSet

from locker_server.core.exceptions.sso_configuration_exception import SSOConfigurationIdentifierExistedException
from .serializers import *
from locker_server.api.permissions.admin_permissions.sso_configuration_permissions import SSOConfigurationPermission


class AdminSSOConfigurationViewSet(APIBaseViewSet):
    permission_classes = (SSOConfigurationPermission,)
    http_method_names = ["options", "head", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9a-z-]+'

    def get_throttles(self):
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "sso_configuration":
            self.serializer_class = DetailSSOConfigurationSerializer
        elif self.action == "update_sso_configuration":
            self.serializer_class = UpdateSSOConfigurationSerializer
        return super().get_serializer_class()

    def get_object(self):
        sso_configuration = self.sso_configuration_service.get_first()
        if sso_configuration:
            self.check_object_permissions(request=self.request, obj=sso_configuration)
            return sso_configuration
        return None

    @action(methods=["get"], detail=False)
    def sso_configuration(self, request, *args, **kwargs):
        sso_configuration = self.get_object()
        if not sso_configuration:
            return Response(status=status.HTTP_200_OK, data={})
        serializer = self.get_serializer(sso_configuration, many=False)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["put"], detail=False)
    def update_sso_configuration(self, request, *args, **kwargs):
        user = request.user
        sso_configuration = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            updated_sso_configuration = self.sso_configuration_service.update_sso_configuration(
                user_id=user.user_id,
                sso_config_update_data={
                    "sso_provider_id": validated_data.get("sso_provider"),
                    "sso_provider_options": json.dumps(validated_data.get("sso_provider_options") or {}),
                    "enabled": validated_data.get("enabled"),
                    "identifier": validated_data.get("identifier"),
                }
            )
        except SSOConfigurationIdentifierExistedException:
            raise ValidationError(detail={"identifier": ["SSO with this identifier already exists"]})
        serializer = DetailSSOConfigurationSerializer(updated_sso_configuration, many=False)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["delete"], detail=False)
    def destroy_sso_configuration(self, request, *args, **kwargs):
        self.get_object()
        self.sso_configuration_service.destroy_sso_configuration()
        return Response(status=status.HTTP_204_NO_CONTENT)
