from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from locker_server.api.api_base_view import APIBaseViewSet

from .serializers import *


class SSOConfigurationViewSet(APIBaseViewSet):
    permission_classes = ()
    http_method_names = ["options", "head", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9a-z-]+'

    def get_throttles(self):
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "get_user_by_code":
            self.serializer_class = RetrieveUserSerializer
        return super().get_serializer_class()

    @action(methods=["post"], detail=False)
    def get_user_by_code(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user_data = self.sso_configuration_service.get_user_by_code(
            sso_identifier=validated_data.get("sso_identifier"),
            code=validated_data.get("code")
        )
        return Response(status=status.HTTP_200_OK, data={"user": user_data})

    @action(methods=["get"], detail=False)
    def check_exists(self, request, *args, **kwargs):
        sso_configuration = self.sso_configuration_service.get_first()
        if sso_configuration:
            serializer = DetailSSOConfigurationSerializer(sso_configuration, many=False)
            sso_configuration_data = serializer.data
            sso_provider_options = sso_configuration_data.get("sso_provider_options")
            sso_provider_options.pop("client_secret", "default")
            sso_configuration_data.update({
                "sso_provider_options": sso_provider_options
            })
            return Response(
                status=status.HTTP_200_OK,
                data={"existed": True, "sso_configuration": sso_configuration_data}
            )
        return Response(status=status.HTTP_200_OK, data={"existed": False})
