from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember
from locker_server.core.entities.user.user import User
from locker_server.core.entities.user_plan.pm_user_plan import PMUserPlan
from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.core.exceptions.enterprise_member_exception import EnterpriseMemberDoesNotExistException, \
    EnterpriseMemberUpdatedFailedException, EnterpriseMemberPrimaryDoesNotExistException
from locker_server.core.exceptions.payment_exception import PaymentMethodNotSupportException
from locker_server.shared.constants.event import EVENT_E_MEMBER_UPDATED_ROLE, EVENT_E_MEMBER_REMOVED, \
    EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_DISABLED, EVENT_E_MEMBER_CONFIRMED
from locker_server.shared.constants.transactions import PAYMENT_METHOD_CARD
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_EVENT
from locker_server.shared.external_services.payment_method.payment_method_factory import PaymentMethodFactory
from locker_server.shared.utils.app import now

from .serializers import *
from locker_server.api.api_base_view import APIBaseViewSet

from locker_server.api.permissions.admin_permissions.admin_enterprise_member_permission import \
    AdminEnterpriseMemberPermission


class AdminEnterpriseMemberViewSet(APIBaseViewSet):
    permission_classes = (AdminEnterpriseMemberPermission,)
    lookup_value_regex = r'[0-9a-z\-]+'
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListMemberSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailMemberSerializer
        elif self.action == "update":
            self.serializer_class = UpdateMemberSerializer
        elif self.action == "activated":
            self.serializer_class = EnabledMemberSerializer
        return super().get_serializer_class()

    def get_enterprise(self):
        try:
            enterprise = self.enterprise_service.get_enterprise_by_id(
                enterprise_id=self.kwargs.get("enterprise_id")
            )
            self.check_object_permissions(request=self.request, obj=enterprise)
            return enterprise
        except EnterpriseDoesNotExistException:
            raise NotFound

    def get_queryset(self):
        enterprise = self.get_enterprise()
        members = self.enterprise_member_service.list_enterprise_members(**{
            "enterprise_id": enterprise.enterprise_id
        })

        return members

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            member = self.enterprise_member_service.get_member_by_id(
                member_id=self.kwargs.get("pk")
            )
            if member.enterprise.enterprise_id != enterprise.enterprise_id:
                raise NotFound
            return member
        except EnterpriseMemberDoesNotExistException:
            raise NotFound

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10

        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        ip = self.get_ip()
        enterprise_member = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            change_status, change_role, updated_member = self.enterprise_member_service.update_enterprise_member(
                current_user=self.request.user,
                enterprise_member=enterprise_member,
                **validated_data
            )
        except EnterpriseMemberDoesNotExistException:
            raise NotFound
        if change_role:
            BackgroundFactory.get_background(bg_name=BG_EVENT).run(
                func_name="create_by_enterprise_ids",
                **{
                    "enterprise_ids": [updated_member.enterprise.enterprise_id],
                    "acting_user_id": self.request.user_id,
                    "user_id": updated_member.user.user_id if updated_member.user else None,
                    "team_member_id": updated_member.enterprise_member_id,
                    "type": EVENT_E_MEMBER_UPDATED_ROLE, "ip_address": ip,
                    "metadata": {"old_role": enterprise_member.role.name, "new_role": updated_member.role.name}
                }
            )

        return Response(
            status=status.HTTP_200_OK,
            data={
                "success": True,
                "change_status": change_status,
                "change_role": change_role,
                "member_id": updated_member.enterprise_member_id,
                "member_user_id": updated_member.user.user_id if updated_member.user else None,
                "enterprise_name": updated_member.enterprise.name,
                "status": updated_member.status,
                "role": updated_member.role.name
            }
        )

    def destroy(self, request, *args, **kwargs):
        ip = self.get_ip()
        user = self.request.user
        enterprise_member = self.get_object()
        enterprise = enterprise_member.enterprise
        deleted_member_user_id = enterprise_member.user.user_id if enterprise_member.user else None
        deleted_member_status = enterprise_member.status
        # Not allow delete themselves
        if enterprise_member.user and enterprise_member.user.user_id == user.user_id:
            raise PermissionDenied
        try:
            self.enterprise_member_service.delete_enterprise_member(
                enterprise_member_id=enterprise_member.enterprise_member_id)
        except EnterpriseMemberDoesNotExistException:
            raise NotFound
        try:
            primary_user = self.enterprise_service.get_primary_member(enterprise_id=enterprise.enterprise_id).user
            current_plan = self.user_service.get_current_plan(user=primary_user)
            PaymentMethodFactory.get_method(
                user_plan=current_plan, scope=settings.SCOPE_PWD_MANAGER,
                payment_method=PAYMENT_METHOD_CARD
            ).update_quantity_subscription(amount=-1)
        except (PaymentMethodNotSupportException, ObjectDoesNotExist):
            pass

        # Log activity delete member here
        BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
            "enterprise_ids": [enterprise.enterprise_id], "acting_user_id": user.user_id,
            "user_id": enterprise_member.user.user_id if enterprise_member.user else None,
            "team_member_id": enterprise_member.enterprise_member_id,
            "type": EVENT_E_MEMBER_REMOVED, "ip_address": ip,
        })

        return Response(
            status=status.HTTP_200_OK,
            data={
                "enterprise_id": enterprise.enterprise_id,
                "enterprise_name": enterprise.name,
                "member_user_id": deleted_member_user_id,
                "member_status": deleted_member_status,
            }
        )

    @action(methods=["put"], detail=True)
    def activated(self, request, *args, **kwargs):
        user = self.request.user
        ip = self.get_ip()
        enterprise_member = self.get_object()
        enterprise = enterprise_member.enterprise
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        activated = validated_data.get("activated")
        if enterprise_member.is_activated != activated:
            try:
                updated_enterprise_member = self.enterprise_member_service.activated_member(
                    activated=activated,
                    enterprise_member=enterprise_member,
                    current_user=user
                )
            except EnterpriseMemberDoesNotExistException:
                raise NotFound
            except EnterpriseMemberUpdatedFailedException:
                raise PermissionDenied
            try:
                primary_user = self.enterprise_service.get_primary_member(enterprise_id=enterprise.enterprise_id).user
            except EnterpriseMemberPrimaryDoesNotExistException:
                primary_user = user
            current_plan = self.user_service.get_current_plan(user=primary_user)
            # Remove this member from all groups
            if activated is False:
                self.enterprise_member_service.delete_group_members_by_member_id(
                    enterprise_member_id=enterprise_member.enterprise_member_id
                )
            #  Update billing here - Check the user is a new activated user in billing period
            if activated is True and self.is_billing_members_added(
                    current_plan=current_plan,
                    enterprise_member=updated_enterprise_member):
                try:
                    PaymentMethodFactory.get_method(
                        user_plan=current_plan, scope=settings.SCOPE_PWD_MANAGER,
                        payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=1)
                except (PaymentMethodNotSupportException, ObjectDoesNotExist):
                    pass
            if activated is False and self.is_billing_members_removed(
                    current_plan=current_plan,
                    enterprise_member=enterprise_member):
                try:
                    PaymentMethodFactory.get_method(
                        user_plan=current_plan, scope=settings.SCOPE_PWD_MANAGER,
                        payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=-1)
                except (PaymentMethodNotSupportException, ObjectDoesNotExist):
                    pass
            BackgroundFactory.get_background(bg_name=BG_EVENT).run(
                func_name="create_by_enterprise_ids",
                **{
                    "enterprise_ids": [enterprise.enterprise_id], "acting_user_id": user.user_id,
                    "user_id": enterprise_member.user.user_id if enterprise_member.user else None,
                    "team_member_id": enterprise_member.enterprise_member_id,
                    "type": EVENT_E_MEMBER_ENABLED if activated is True else EVENT_E_MEMBER_DISABLED,
                    "ip_address": ip
                })
            return Response(
                status=status.HTTP_200_OK,
                data={
                    "success": True, "notification": True,
                    "member_user_id": enterprise_member.user.user_id if enterprise_member.user else None,
                    "enterprise_name": enterprise_member.enterprise.name,
                    "activated": activated
                }
            )

        return Response(status=status.HTTP_200_OK, data={"success": True})

    def is_billing_members_added(self, current_plan: PMUserPlan, enterprise_member: EnterpriseMember) -> bool:
        enterprise = enterprise_member.enterprise
        from_param = current_plan.start_period if current_plan.start_period else enterprise.creation_date
        to_param = current_plan.end_period if current_plan.end_period else now()
        events = self.event_service.list_events(**{
            "team_id": enterprise.enterprise_id,
            "types": [EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_CONFIRMED],
            "user_id": enterprise_member.user.user_id if enterprise_member.user else None,
            "from": from_param,
            "to": to_param,
            "creation_date_range": (from_param, to_param)
        })
        if not events:
            return True
        return False

    def is_billing_members_removed(self, current_plan: PMUserPlan, enterprise_member: EnterpriseMember) -> bool:
        enterprise = enterprise_member.enterprise
        from_param = current_plan.start_period if current_plan.start_period else enterprise.creation_date
        to_param = current_plan.end_period if current_plan.end_period else now()
        events = self.event_service.list_events(**{
            "team_id": enterprise.enterprise_id,
            "types": [EVENT_E_MEMBER_DISABLED, EVENT_E_MEMBER_REMOVED],
            "user_id": enterprise_member.user.user_id if enterprise_member.user else None,
            "from": from_param,
            "to": to_param,
            "creation_date_range": (from_param, to_param)
        })
        if not events:
            return True
        return False
