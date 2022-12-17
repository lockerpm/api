from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError

from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.team_event_pwd_permission import TeamEventPwdPermission
from shared.utils.app import now
from v1_0.enterprise.activity_logs.serializers import EventSerializer
from v1_0.general_view import PasswordManagerViewSet


class ActivityLogViewSet(PasswordManagerViewSet):
    permission_classes = (TeamEventPwdPermission, )
    http_method_names = ["head", "options", "get"]
    serializer_class = EventSerializer

    def get_serializer_class(self):
        return super(ActivityLogViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            team = self.team_repository.get_vault_team_by_id(team_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=team)
            if self.team_repository.is_locked(team=team):
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
            team = self.allow_team_plan(team=team)
            return team
        except ObjectDoesNotExist:
            raise NotFound

    def allow_team_plan(self, team):
        primary_user = self.team_repository.get_primary_member(team=team).user
        current_plan = self.user_repository.get_current_plan(user=primary_user)
        plan_obj = current_plan.get_plan_obj()
        if plan_obj.allow_team_activity_log() is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        return team

    def get_queryset(self):
        team = self.get_object()
        to_param = self.check_int_param(self.request.query_params.get("to", now()))
        from_param = self.check_int_param(self.request.query_params.get("from", now() - 30 * 86400))
        if not to_param:
            to_param = now()
        if not from_param:
            from_param = now() - 30 * 86400

        events = self.event_repository.get_multiple_by_team_id(team_id=team.id).filter(
            creation_date__lte=to_param,
            creation_date__gte=from_param
        )
        return events

    def list(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 50))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 50
        return super(ActivityLogViewSet, self).list(request, *args, **kwargs)
