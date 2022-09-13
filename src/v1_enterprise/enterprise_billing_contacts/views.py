from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.enterprises.payments.billing_contacts import EnterpriseBillingContact
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.enterprises.groups.groups import EnterpriseGroup
from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.constants.event import EVENT_E_GROUP_CREATED, EVENT_E_GROUP_UPDATED, EVENT_E_GROUP_DELETED
from shared.constants.enterprise_members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.billing_contact_permission import BillingContractPwdPermission
from shared.permissions.locker_permissions.enterprise.group_permission import GroupPwdPermission
from shared.utils.app import now, diff_list
from v1_enterprise.apps import EnterpriseViewSet
from v1_enterprise.enterprise_members.serializers import DetailMemberSerializer
from .serializers import EnterpriseBillingContactSerializer


class BillingContactViewSet(EnterpriseViewSet):
    permission_classes = (BillingContractPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    serializer_class = EnterpriseBillingContactSerializer

    def get_serializer_class(self):
        return super(BillingContactViewSet, self).get_serializer_class()

    def get_queryset(self):
        enterprise = self.get_enterprise()
        billing_contacts = enterprise.billing_contacts.all().order_by('-created_time')
        return billing_contacts

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            billing_contact = enterprise.billing_contacts.get(id=self.kwargs.get("contact_id"))
            return billing_contact
        except EnterpriseBillingContact.DoesNotExist:
            raise NotFound

    def get_enterprise(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return enterprise
        except Enterprise.DoesNotExist:
            raise NotFound

    def list(self, request, *args, **kwargs):
        self.pagination_class = None
        return super(BillingContactViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        new_contact = EnterpriseBillingContact.retrieve_or_create(enterprise=enterprise, email=email)
        return Response(status=201, data={"id": new_contact.id})

    def destroy(self, request, *args, **kwargs):
        return super(BillingContactViewSet, self).destroy(request, *args, **kwargs)



