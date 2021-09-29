from rest_framework.response import Response
from rest_framework.decorators import action

from micro_services.apps import MicroServiceViewSet
from shared.constants.members import MEMBER_ROLE_OWNER
from shared.permissions.micro_service_permissions.sync_permissions import SyncPermission
from cystack_models.models.teams.teams import Team
from cystack_models.models.members.member_roles import MemberRole


class SyncTeamViewSet(MicroServiceViewSet):
    permission_classes = (SyncPermission,)
    lookup_value_regex = r'[0-9a-z\-]+'
    http_method_names = ['head', 'options', 'get', 'post', 'put', 'delete']

    def get_serializer_class(self):
        return super(SyncTeamViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def sync_list(self, request, *args, **kwargs):
        """
        Create list default teams from CSP
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        user = self.request.user
        teams = request.data
        team_ids = [team.get("id") for team in teams]
        existed_teams = list(Team.objects.filter(id__in=team_ids).values_list('id', flat=True))
        for team in teams:
            if team.get("id") in existed_teams:
                continue
            team["members"] = [{
                "user": user,
                "role": MemberRole.objects.get(name=MEMBER_ROLE_OWNER),
                "is_default": team.get("is_default", False),
                "is_primary": True
            }]
            Team.create(**team)

        return Response(status=200, data={"success": True})
