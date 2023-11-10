from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from locker_server.core.exceptions.enterprise_billing_contact_exception import \
    EnterpriseBillingContactDoesNotExistException
from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.shared.error_responses.error import gen_error
from .serializers import *
from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.enterprise_permissions.billing_contact_pwd_permission import \
    BillingContactPwdPermission


class BillingContactViewSet(APIBaseViewSet):
    permission_classes = (BillingContactPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListEnterpriseBillingContactSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailEnterpriseBillingContactSerializer
        elif self.action == "create":
            self.serializer_class = CreateEnterpriseBillingContactSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        enterprise = self.get_enterprise()
        billing_contacts = self.enterprise_billing_contact_service.list_enterprise_billing_contacts(
            enterprise_id=enterprise.enterprise_id
        )

        return billing_contacts

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            billing_contact = self.enterprise_billing_contact_service.get_enterprise_billing_contact_by_id(
                enterprise_billing_contact_id=self.kwargs.get("contact_id")
            )
            if billing_contact.enterprise.enterprise_id != enterprise.enterprise_id:
                raise NotFound
            return billing_contact
        except EnterpriseBillingContactDoesNotExistException:
            raise NotFound

    def get_enterprise(self):
        try:
            enterprise = self.enterprise_service.get_enterprise_by_id(
                enterprise_id=self.kwargs.get("pk")
            )
            self.check_object_permissions(request=self.request, obj=enterprise)
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return enterprise
        except EnterpriseDoesNotExistException:
            raise NotFound

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        self.pagination_class = None
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        new_contact = self.enterprise_billing_contact_service.create_enterprise_billing_contact(
            enterprise_id=enterprise.enterprise_id,
            email=email
        )
        return Response(status=status.HTTP_201_CREATED, data={"id": new_contact.enterprise_billing_contact_id})

    def destroy(self, request, *args, **kwargs):
        billing_contact = self.get_object()
        try:
            self.enterprise_billing_contact_service.delete_enterprise_billing_contact_by_id(
                billing_contact_id=billing_contact.en
            )
        except EnterpriseBillingContactDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_204_NO_CONTENT)
