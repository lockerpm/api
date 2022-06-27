from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField, Count, Avg
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models import Team
from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.constants.ciphers import *
from shared.constants.event import EVENT_TEAM_PURGED_DATA, EVENT_TEAM_UPDATED
from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.team_pwd_permission import TeamPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_VAULT
from v1_0.enterprise_v2.teams.serializers import ListTeamSerializer
from v1_0.apps import PasswordManagerViewSet


class EnterpriseTeamPWDViewSet(PasswordManagerViewSet):
    permission_classes = (TeamPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            self.serializer_class = ListTeamSerializer
        return super(EnterpriseTeamPWDViewSet, self).get_serializer_class()
    
    def get_object(self):
        try:
            team = Team.objects.get(id=self.kwargs.get("pk"), personal_share=False)
            self.check_object_permissions(request=self.request, obj=team)
            if self.action in ["update", "import_data", "dashboard"]:
                if team.locked:
                    raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return team
        except ObjectDoesNotExist:
            raise NotFound
    
    def allow_team_plan(self, team):
        primary_user = team.team_members.get(is_primary=True).user
        current_plan = self.user_repository.get_current_plan(user=primary_user)
        plan_obj = current_plan.get_plan_obj()
        if self.action == "dashboard":
            if plan_obj.allow_team_dashboard() is False:
                raise ValidationError({"non_field_errors": [gen_error("7002")]})

        return team
    
    def get_queryset(self):
        order_whens = [
            When(Q(team_members__is_default=True), then=Value(1)),
        ]
        user = self.request.user
        teams = Team.objects.filter(
            team_members__user=user, key__isnull=False, personal_share=False, 
            team_members__status=PM_MEMBER_STATUS_CONFIRMED
        ).annotate(
            is_default=Case(*order_whens, output_field=IntegerField(), default=Value(0))
        ).order_by('-is_default', '-creation_date')
        return teams
    
    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.pagination_class = None
        return super(EnterpriseTeamPWDViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super(EnterpriseTeamPWDViewSet, self).retrieve(request, *args, **kwargs)

