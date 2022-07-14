from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField, Count, Avg
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.constants.ciphers import *
from shared.constants.event import EVENT_TEAM_PURGED_DATA, EVENT_TEAM_UPDATED
from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.team_pwd_permission import TeamPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_VAULT
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import ListTeamSerializer, UpdateTeamSerializer


class TeamPwdViewSet(EnterpriseViewSet):
    permission_classes = (TeamPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            self.serializer_class = ListTeamSerializer
        elif self.action in ["update"]:
            self.serializer_class = UpdateTeamSerializer

        return super(TeamPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            team = self.team_repository.get_by_id(team_id=self.kwargs.get("pk"))
        except ObjectDoesNotExist:
            raise NotFound
        if team.personal_share:
            raise NotFound
        self.check_object_permissions(request=self.request, obj=team)
        if self.action in ["update", "import_data", "dashboard"]:
            if self.team_repository.is_locked(team=team):
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
        return team

    def allow_team_plan(self, team):
        primary_user = self.team_repository.get_primary_member(team=team).user
        current_plan = self.user_repository.get_current_plan(user=primary_user)
        plan_obj = current_plan.get_plan_obj()
        if self.action == "dashboard":
            if plan_obj.allow_team_dashboard() is False:
                raise ValidationError({"non_field_errors": [gen_error("7002")]})

        return team

    def get_queryset(self):
        order_whens = [
            When(Q(team_members__is_default=True), then=Value(1))
        ]
        user = self.request.user
        teams = self.team_repository.get_multiple_team_by_user(
            user=user, status=PM_MEMBER_STATUS_CONFIRMED, personal_share=False
        ).annotate(
            is_default=Case(*order_whens, output_field=IntegerField(), default=Value(0))
        ).order_by('-is_default', '-creation_date')
        return teams

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.pagination_class = None
        return super(TeamPwdViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super(TeamPwdViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        team = self.get_object()
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
            "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
            "type": EVENT_TEAM_UPDATED, "ip_address": ip
        })
        return super(TeamPwdViewSet, self).update(request, *args, **kwargs)

    @action(methods=["post"], detail=True)
    def purge(self, request, *args, **kwargs):
        # -------- [COMING SOON] ---------- #
        raise NotFound

        # user = self.request.user
        # ip = request.data.get("ip")
        # team = self.get_object()
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
        #     "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_TEAM_PURGED_DATA, "ip_address": ip
        # })
        # return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def import_data(self, request, *args, **kwargs):
        # ----------- [COMING SOON] ------------- #
        raise NotFound

    @action(methods=["get"], detail=True)
    def dashboard(self, request, *args, **kwargs):
        # ---------- [COMING SOON] ------------- #
        raise NotFound
