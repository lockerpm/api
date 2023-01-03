from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from core.utils.data_helpers import convert_readable_date
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.events.events import Event
from shared.constants.enterprise_members import *
from shared.constants.event import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.activity_log_permission import ActivityLogPwdPermission
from shared.utils.app import now
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import ActivityLogSerializer, ExportEmailActivityLogSerializer


class ActivityLogPwdViewSet(EnterpriseViewSet):
    permission_classes = (ActivityLogPwdPermission, )
    http_method_names = ["head", "options", "get", "post"]
    serializer_class = ActivityLogSerializer

    def get_serializer_class(self):
        if self.action == "export_to_email":
            self.serializer_class = ExportEmailActivityLogSerializer
        return super(ActivityLogPwdViewSet, self).get_serializer_class()

    def get_enterprise(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
            enterprise = self.check_allow_plan(enterprise=enterprise)
            return enterprise
        except Enterprise.DoesNotExist:
            raise NotFound

    def check_allow_plan(self, enterprise):
        primary_user = enterprise.enterprise_members.get(is_primary=True).user
        current_plan = self.user_repository.get_current_plan(user=primary_user)
        plan_obj = current_plan.get_plan_obj()
        if plan_obj.allow_team_activity_log() is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        return enterprise

    def get_queryset(self):
        enterprise = self.get_enterprise()
        to_param = self.check_int_param(self.request.query_params.get("to")) or now()
        from_param = self.check_int_param(self.request.query_params.get("from")) or now() - 30 * 86400
        admin_only_param = self.request.query_params.get("admin_only", "0")
        member_only_param = self.request.query_params.get("member_only", "0")
        group_param = self.request.query_params.get("group")
        member_ids_param = self.request.query_params.get("member_ids")
        acting_member_ids_param = self.request.query_params.get("acting_member_ids")
        action_param = self.request.query_params.get("action")

        events = Event.objects.filter(team_id=enterprise.id).order_by('-creation_date').filter(
            creation_date__lte=to_param,
            creation_date__gte=from_param
        )
        if admin_only_param == "1":
            admin_user_ids = list(enterprise.enterprise_members.filter(
                role_id__in=[E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
            ).values_list('user_id', flat=True))
            events = events.filter(Q(acting_user_id__in=admin_user_ids) | Q(user_id__in=admin_user_ids)).distinct()
        if member_only_param == "1":
            member_user_ids = list(enterprise.enterprise_members.filter(
                role_id__in=[E_MEMBER_ROLE_MEMBER]
            ).values_list('user_id', flat=True))
            events = events.filter(Q(acting_user_id__in=member_user_ids) | Q(user_id__in=member_user_ids)).distinct()
        if member_ids_param:
            member_user_ids = list(enterprise.enterprise_members.filter(
                id__in=member_ids_param.split(",")
            ).values_list('user_id', flat=True))
            events = events.filter(Q(acting_user_id__in=member_user_ids) | Q(user_id__in=member_user_ids)).distinct()
        if acting_member_ids_param:
            member_user_ids = list(enterprise.enterprise_members.filter(
                id__in=acting_member_ids_param.split(",")
            ).values_list('user_id', flat=True))
            events = events.filter(acting_user_id__in=member_user_ids).distinct()
        if group_param:
            member_user_ids = list(
                enterprise.groups.filter(id=group_param).values_list('groups_members__member__user_id', flat=True)
            )
            events = events.filter(Q(acting_user_id__in=member_user_ids) | Q(user_id__in=member_user_ids)).distinct()
        if action_param:
            if action_param == "member_changes":
                events = events.filter(type__in=[
                    EVENT_E_MEMBER_INVITED, EVENT_E_MEMBER_CONFIRMED, EVENT_E_MEMBER_REMOVED,
                    EVENT_E_MEMBER_UPDATED_GROUP, EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_DISABLED
                ])
            elif action_param == "role_changes":
                events = events.filter(type__in=[EVENT_E_MEMBER_UPDATED_ROLE])
            elif action_param == "policy_violations":
                events = events.filter(type__in=[EVENT_USER_BLOCK_LOGIN])
            elif action_param == "user_login":
                events = events.filter(type__in=[EVENT_USER_LOGIN, EVENT_USER_LOGIN_FAILED])
            elif action_param == "member_billing_changes":
                events = events.filter(type__in=[
                    EVENT_E_MEMBER_CONFIRMED, EVENT_E_MEMBER_REMOVED, EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_DISABLED
                ])
        return events

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        page = self.paginate_queryset(queryset)
        if page is not None:
            logs = Event.objects.filter(id__in=[p.id for p in page]).order_by('-creation_date')
            normalize_page = self.event_repository.normalize_enterprise_activity(activity_logs=logs)
            return self.get_paginated_response(normalize_page)
        logs = self.event_repository.normalize_enterprise_activity(activity_logs=queryset)
        return Response(status=200, data=logs)

    @action(methods=["get"], detail=False)
    def export(self, request, *args, **kwargs):
        activity_logs_qs = self.get_queryset()
        enterprise = self.get_enterprise()
        enterprise_member = enterprise.enterprise_members.get(user=self.request.user)
        self.event_repository.export_enterprise_activity(
            enterprise_member=enterprise_member, activity_logs=activity_logs_qs
        )
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def export_to_email(self, request, *args, **kwargs):
        to_param = self.check_int_param(self.request.query_params.get("to")) or now()
        from_param = self.check_int_param(self.request.query_params.get("from")) or now() - 30 * 86400
        to_param_str = convert_readable_date(to_param, "%m/%d/%Y %H:%M:%S") + " (UTC+00)"
        from_param_str = convert_readable_date(from_param, "%m/%d/%Y %H:%M:%S") + " (UTC+00)"

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        activity_logs_qs = self.get_queryset()
        enterprise = self.get_enterprise()
        enterprise_member = enterprise.enterprise_members.get(user=self.request.user)
        self.event_repository.export_enterprise_activity(
            enterprise_member=enterprise_member,
            activity_logs=activity_logs_qs,
            cc_emails=validated_data.get("cc", []),
            **{"to": to_param_str, "from": from_param_str}
        )
        return Response(status=200, data={"success": True})
