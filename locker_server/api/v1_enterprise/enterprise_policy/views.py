from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.core.exceptions.enterprise_policy_exception import EnterprisePolicyDoesNotExistException
from locker_server.shared.background.i_background import background_exception_wrapper, BackgroundThread
from locker_server.shared.constants.policy import POLICY_TYPE_PASSWORD_REQUIREMENT, \
    POLICY_TYPE_MASTER_PASSWORD_REQUIREMENT, POLICY_TYPE_BLOCK_FAILED_LOGIN, POLICY_TYPE_PASSWORDLESS, POLICY_TYPE_2FA
from locker_server.shared.error_responses.error import gen_error
from .serializers import *
from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.enterprise_permissions.policy_pwd_permission import \
    PolicyPwdPermission


class PolicyPwdViewSet(APIBaseViewSet):
    permission_classes = (PolicyPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListPolicySerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailPolicySerializer
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
        try:
            policies = self.enterprise_service.list_enterprise_policies(
                enterprise_id=enterprise.enterprise_id
            )
        except EnterpriseDoesNotExistException:
            raise NotFound
        return policies

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            policy = self.enterprise_service.get_policy_by_type(
                enterprise_id=enterprise.enterprise_id,
                policy_type=self.kwargs.get("policy_type")
            )
        except EnterprisePolicyDoesNotExistException:
            raise NotFound
        return policy

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

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "0")
        size_param = self.request.query_params.get("size", 10)
        page_size_param = self.check_int_param(size_param)
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param or 10
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        policy = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        self.enterprise_service.update_policy(
            policy=policy,
            policy_update_data=validated_data
        )
        BackgroundThread(task=self.delete_cache_enterprise_members, **{"enterprise": policy.enterprise})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @background_exception_wrapper
    def delete_cache_enterprise_members(self, enterprise):
        user_ids = self.enterprise_member_service.list_enterprise_member_user_ids(**{
            "enterprise_id": enterprise.enterprise_id
        })
        for user_id in user_ids:
            if not user_id:
                continue
            self.user_service.delete_sync_cache_data(user_id=user_id)

