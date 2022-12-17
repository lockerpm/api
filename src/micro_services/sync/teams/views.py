from rest_framework.response import Response
from rest_framework.decorators import action

from micro_services.general_view import MicroServiceViewSet
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

        # If the default team of the user existed => Return
        user_default_team = self.user_repository.get_default_team(user=user)
        if user_default_team:
            return Response(status=200, data={"success": True})

        teams = request.data
        # Get default team from data
        team_ids = [team.get("id") for team in teams]
        default_teams = [team for team in teams if team.get("is_default") is True]
        if len(default_teams) != 1:
            return Response(status=200, data={"success": True})

        # Check this default team is existed
        existed_teams = list(Team.objects.filter(id__in=team_ids).values_list('id', flat=True))
        default_team_data = default_teams[0]
        if default_team_data.get("id") in existed_teams:
            return Response(status=200, data={"success": True})

        # Create default team here
        default_team_data["members"] = [{
            "user": user,
            "role": MemberRole.objects.get(name=MEMBER_ROLE_OWNER),
            "is_default": True,
            "is_primary": True
        }]
        Team.create(**default_team_data)
        return Response(status=200, data={"success": True})
