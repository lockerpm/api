from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.enterprises.enterprises import Enterprise
from shared.background.i_background import BackgroundThread, background_exception_wrapper
from shared.caching.sync_cache import delete_sync_cache_data
from shared.constants.policy import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.policy_permission import PolicyPwdPermission
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import PolicySerializer, UpdatePasswordPolicySerializer, UpdateMasterPasswordPolicySerializer, \
    UpdateFailedLoginPolicySerializer, UpdatePasswordlessPolicySerializer, Update2FAPolicySerializer


class PolicyPwdViewSet(EnterpriseViewSet):
    permission_classes = (PolicyPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            self.serializer_class = PolicySerializer
        elif self.action == "update":
            policy_type = self.kwargs.get("policy_type")
            if policy_type == POLICY_TYPE_PASSWORD_REQUIREMENT:
                self.serializer_class = UpdatePasswordPolicySerializer
            elif policy_type == POLICY_TYPE_MASTER_PASSWORD_REQUIREMENT:
                self.serializer_class = UpdateMasterPasswordPolicySerializer
            elif policy_type == POLICY_TYPE_BLOCK_FAILED_LOGIN:
                self.serializer_class = UpdateFailedLoginPolicySerializer
            elif policy_type == POLICY_TYPE_PASSWORDLESS:
                self.serializer_class = UpdatePasswordlessPolicySerializer
            elif policy_type == POLICY_TYPE_2FA:
                self.serializer_class = Update2FAPolicySerializer
        return super(PolicyPwdViewSet, self).get_serializer_class()

    def get_queryset(self):
        enterprise = self.get_enterprise()
        if enterprise.policies.count() < len(LIST_POLICY_TYPE):
            for policy_type in LIST_POLICY_TYPE:
                enterprise.policies.model.retrieve_or_create(enterprise, policy_type)
        policies = enterprise.policies.all().order_by('id')
        return policies

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            policy = enterprise.policies.get(policy_type=self.kwargs.get("policy_type"))
        except ObjectDoesNotExist:
            raise NotFound
        return policy

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
        paging_param = self.request.query_params.get("paging", "0")
        if paging_param == "0":
            self.pagination_class = None
        return super(PolicyPwdViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super(PolicyPwdViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        policy = self.get_object()
        config_obj = policy.get_config_obj()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(**{"config_obj": config_obj})
        BackgroundThread(task=self.delete_cache_enterprise_members, **{"enterprise": policy.enterprise})
        return Response(status=200, data={"success": True})

    @background_exception_wrapper
    def delete_cache_enterprise_members(self, enterprise):
        user_ids = list(enterprise.enterprise_members.exclude(user_id__isnull=True).values_list('user_id', flat=True))
        for user_id in user_ids:
            delete_sync_cache_data(user_id=user_id)
