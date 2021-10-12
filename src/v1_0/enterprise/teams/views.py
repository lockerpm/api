from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

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
        all_teams = self.team_repository.get_multiple_team_by_user(user=user).annotate(
            is_default=Case(*order_whens, output_field=IntegerField(), default=Value(0))
        ).order_by('-is_default', '-creation_date')
        return all_teams

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.serializer_class = None
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
        pass
