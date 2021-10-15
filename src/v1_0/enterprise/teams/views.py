from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField, Count, Avg
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.constants.ciphers import *
from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.team_pwd_permission import TeamPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_DELETE, SYNC_EVENT_CIPHER_CREATE, \
    SYNC_EVENT_CIPHER_UPDATE
from v1_0.enterprise.teams.serializers import ListTeamSerializer, UpdateTeamPwdSerializer
from v1_0.apps import PasswordManagerViewSet


class TeamPwdViewSet(PasswordManagerViewSet):
    permission_classes = (TeamPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            self.serializer_class = ListTeamSerializer
        elif self.action in ["update"]:
            self.serializer_class = UpdateTeamPwdSerializer
        return super(TeamPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            team = self.team_repository.get_by_id(team_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=team)
            if self.action in ["update", "import_data", "dashboard"]:
                if self.team_repository.is_locked(team=team):
                    raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return team
        except ObjectDoesNotExist:
            raise NotFound

    def get_queryset(self):
        order_whens = [
            When(Q(team_members__is_default=True), then=Value(1)),
        ]
        user = self.request.user
        all_teams = self.team_repository.get_multiple_team_by_user(
            user=user, status=PM_MEMBER_STATUS_CONFIRMED
        ).annotate(
            is_default=Case(*order_whens, output_field=IntegerField(), default=Value(0))
        ).order_by('-is_default', '-creation_date')
        return all_teams

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.pagination_class = None
        return super(TeamPwdViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super(TeamPwdViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        return super(TeamPwdViewSet, self).update(request, *args, **kwargs)

    @action(methods=["post"], detail=False)
    def purge(self, request, *args, **kwargs):
        pass

    @action(methods=["post"], detail=False)
    def import_data(self, request, *args, **kwargs):
        pass

    @action(methods=["get"], detail=False)
    def dashboard(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        team = self.get_object()

        # Items statistic
        ciphers = team.ciphers.all()
        login_ciphers = ciphers.filter(type=CIPHER_TYPE_LOGIN)

        item_statistic = {
            "total": ciphers.count(),
            "trash": ciphers.filter(deleted_date__isnull=False).count(),
            "login": login_ciphers.count(),
            "secure_note": ciphers.filter(type=CIPHER_TYPE_NOTE).count(),
            "card": ciphers.filter(type=CIPHER_TYPE_CARD).count(),
            "identity":  ciphers.filter(type=CIPHER_TYPE_IDENTITY).count()
        }

        # Member statistic
        members = team.team_members.filter()
        members_role_count = members.values('role_id').annotate(count=Count('role_id'))
        members_role_statistic = {
            MEMBER_ROLE_OWNER: 0,
            MEMBER_ROLE_ADMIN: 0,
            MEMBER_ROLE_MANAGER: 0,
            MEMBER_ROLE_MEMBER: 0,
        }
        for mem in members_role_count:
            members_role_statistic.update({mem["role_id"]: mem["count"]})
        members_status_count = members.values('status').annotate(count=Count('status'))
        members_status_statistic = {
            PM_MEMBER_STATUS_CONFIRMED: 0,
            PM_MEMBER_STATUS_ACCEPTED: 0,
            PM_MEMBER_STATUS_INVITED: 0,
        }
        for mem in members_status_count:
            members_status_statistic.update({mem["status"]: mem["count"]})

        # Password statistic
        ciphers_score_count = ciphers.values('score').annotate(count=Count('score')).order_by('-score')
        ciphers_score_avg = ciphers.values('score').aggregate(avg=Avg('score'))
        master_password_weak_count = members.filter(user__master_password_score__lte=1).count()

        # Return Results
        return Response(status=200, data={
            "items": item_statistic,
            "members": {
                "total": members.count(),
                "roles": members_role_statistic,
                "status": members_status_statistic
            },
            "master_password": {
                'weak': master_password_weak_count
            },
            "login": {
                "total": login_ciphers.count(),
                "scores": ciphers_score_count,
                "avg_score": ciphers_score_avg.get("avg")
            }
        })