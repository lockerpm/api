import json

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.admin_permissions.admin_mail_configuration_permission import \
    AdminMailConfigurationPermission
from .serializers import MailConfigurationSerializer, UpdateMailConfigurationSerializer, SendTestMailSerializer


class AdminMailConfigurationViewSet(APIBaseViewSet):
    permission_classes = (AdminMailConfigurationPermission,)
    http_method_names = ["options", "head", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9a-z]+'

    def get_throttles(self):
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "mail_configuration":
            self.serializer_class = MailConfigurationSerializer
        elif self.action == "update_mail_configuration":
            self.serializer_class = UpdateMailConfigurationSerializer
        elif self.action == "send_test_mail":
            self.serializer_class = SendTestMailSerializer
        return super().get_serializer_class()

    def get_object(self):
        mail_configuration = self.mail_configuration_service.get_mail_configuration()
        self.check_object_permissions(request=self.request, obj=mail_configuration)
        return mail_configuration

    @action(methods=["get"], detail=False)
    def mail_configuration(self, request, *args, **kwargs):
        org_mail_configuration = self.get_object()
        if not org_mail_configuration:
            return Response(status=status.HTTP_200_OK, data={})
        serializer = self.get_serializer(org_mail_configuration, many=False)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["put"], detail=False)
    def update_mail_configuration(self, request, *args, **kwargs):
        self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        org_mail_configuration = self.mail_configuration_service.update_mail_configuration(
            mail_config_data={
                "mail_provider_id": validated_data.get("mail_provider"),
                "mail_provider_options": json.dumps(validated_data.get("mail_provider_options") or {}),
                "sending_domain": validated_data.get("sending_domain"),
                "from_email": validated_data.get("from_email"),
                "from_name": validated_data.get("from_name")
            }
        )
        serializer = MailConfigurationSerializer(org_mail_configuration, many=False)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["delete"], detail=False)
    def destroy_mail_configuration(self, request, *args, **kwargs):
        self.get_object()
        self.mail_configuration_service.destroy_mail_configuration()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post"], detail=False)
    def send_test_mail(self, request, *args, **kwargs):
        # user = self.request.user
        # try:
        #     organization = self.organization_service.get_organization_by_id(organization_id=self.kwargs.get("pk"))
        #     self.check_object_permissions(request=self.request, obj=organization)
        # except OrganizationDoesNotExistException:
        #     raise NotFound
        # org_mail_config = self.org_mail_configuration_service.get_org_mail_configuration(
        #     organization_id=organization.organization_id
        # )
        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # validated_data = serializer.validated_data
        # email = validated_data.get("email") or user.username
        # NotificationSender(
        #     job=SECRETS_TEST_MAIL, background=False, organization_id=organization.organization_id
        # ).send(**{
        #     "destinations": [{"email": email, "name": user.full_name, "language": user.language}],
        #     "method": org_mail_config.mail_provider.name if org_mail_config else None
        # })
        return Response(status=status.HTTP_200_OK, data={"success": True})
