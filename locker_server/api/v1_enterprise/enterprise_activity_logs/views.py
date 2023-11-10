from typing import List

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.enterprise_permissions.activity_log_pwd_permission import \
    ActivityLogPwdPermission
from locker_server.core.entities.event.event import Event
from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.core.exceptions.enterprise_member_exception import EnterpriseMemberPrimaryDoesNotExistException
from locker_server.shared.background.i_background import BackgroundThread
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.requester.retry_requester import requester
from locker_server.shared.utils.app import convert_readable_date, now
from .serializers import *


class ActivityLogPwdViewSet(APIBaseViewSet):
    permission_classes = (ActivityLogPwdPermission,)
    http_method_names = ["head", "options", "get", "post"]

    def get_serializer_class(self):
        if self.action == "export_to_email":
            self.serializer_class = ExportEmailActivityLogSerializer
        return super().get_serializer_class()

    def get_enterprise(self):
        try:
            enterprise = self.enterprise_service.get_enterprise_by_id(
                enterprise_id=self.kwargs.get("pk")
            )
            self.check_object_permissions(request=self.request, obj=enterprise)
            enterprise = self.check_allow_plan(enterprise=enterprise)
            return enterprise
        except EnterpriseDoesNotExistException:
            raise NotFound

    def check_allow_plan(self, enterprise):
        try:
            primary_member = self.enterprise_service.get_primary_member(
                enterprise_id=enterprise.enterprise_id
            )
        except EnterpriseMemberPrimaryDoesNotExistException:
            raise NotFound
        current_plan = self.user_service.get_current_plan(user=primary_member.user)
        plan = current_plan.pm_plan
        if plan.team_activity_log is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        return enterprise

    def get_queryset(self):
        enterprise = self.get_enterprise()
        filters = {
            "team_id": enterprise.enterprise_id,
            "to": self.check_int_param(self.request.query_params.get("to")) or now(),
            "from": self.check_int_param(self.request.query_params.get("from")) or now() - 30 * 86400,
            "admin_only": self.request.query_params.get("admin_only", "0"),
            "member_only": self.request.query_params.get("member_only", "0"),
            "group": self.request.query_params.get("group"),
            "member_ids": self.request.query_params.get("member_ids"),
            "acting_member_ids": self.request.query_params.get("acting_member_ids"),
            "action": self.request.query_params.get("action"),
        }
        events = self.event_service.list_events(**filters)
        return events

    def get_users_data(self, activity_logs: List[Event]):
        user_ids = [activity_log.user_id for activity_log in activity_logs if activity_log.user_id]
        acting_user_ids = [activity_log.acting_user_id for activity_log in activity_logs if activity_log.acting_user_id]
        query_user_ids = list(set(list(user_ids) + list(acting_user_ids)))

        if settings.SELF_HOSTED:
            users = self.user_service.list_user_by_ids(user_ids=query_user_ids)
            users_data = [{
                "id": user.user_id,
                "name": user.full_name,
                "email": user.email,
                "username": user.username,
                "avatar": user.get_avatar(),
            } for user in users]
        else:
            url = "{}/micro_services/users".format(settings.GATEWAY_API)
            headers = {'Authorization': settings.MICRO_SERVICE_USER_AUTH}
            data_send = {"ids": user_ids, "emails": []}
            res = requester(method="POST", url=url, headers=headers, data_send=data_send, retry=True)
            if res.status_code == 200:
                users_data = res.json()
            else:
                users_data = []
        users_data_dict = dict()
        for user_data in users_data:
            users_data_dict[user_data.get("id")] = user_data
        return users_data_dict

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
            normalize_page = self.event_service.normalize_enterprise_activity(
                activity_logs=page, users_data_dict=self.get_users_data(page)
            )
            return self.get_paginated_response(normalize_page)
        logs = self.event_service.normalize_enterprise_activity(
            activity_logs=queryset, users_data_dict=self.get_users_data(queryset)
        )
        return Response(status=status.HTTP_200_OK, data=logs)

    @action(methods=["get"], detail=False)
    def export(self, request, *args, **kwargs):
        activity_logs_qs = self.get_queryset()
        enterprise = self.get_enterprise()
        enterprise_member = self.enterprise_member_service.get_member_by_user(
            user_id=request.user.user_id,
            enterprise_id=enterprise.enterprise_id
        )
        activity_logs = self.event_service.normalize_enterprise_activity(
            activity_logs=activity_logs_qs,
            users_data_dict=self.get_users_data(activity_logs=activity_logs_qs),
            use_html=False
        )
        # If self-hosted => Only support export to local storage
        if settings.SELF_HOSTED:
            BackgroundThread(task=self.event_service.export_enterprise_activity_job_local, **{
                "activity_logs": activity_logs
            })
        else:
            self.event_service.export_enterprise_activity(
                enterprise_member=enterprise_member, activity_logs=activity_logs
            )
        return Response(status=status.HTTP_200_OK, data={"success": True})

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
        enterprise_member = self.enterprise_member_service.get_member_by_user(
            user_id=request.user.user_id,
            enterprise_id=enterprise.enterprise_id
        )
        activity_logs = self.event_service.normalize_enterprise_activity(
            activity_logs=activity_logs_qs,
            users_data_dict=self.get_users_data(activity_logs=activity_logs_qs),
            use_html=False
        )
        if settings.SELF_HOSTED:
            BackgroundThread(task=self.event_service.export_enterprise_activity_job_local, **{
                "activity_logs": activity_logs
            })
        else:
            self.event_service.export_enterprise_activity(
                enterprise_member=enterprise_member,
                activity_logs=activity_logs,
                cc_emails=validated_data.get("cc", []),
                **{"to": to_param_str, "from": from_param_str}
            )
        return Response(status=status.HTTP_200_OK, data={"success": True})
