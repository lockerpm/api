from django.db.models import Q

from core.repositories import ITeamMemberRepository

from shared.utils.app import now
from shared.constants.members import *
from cystack_models.models.members.team_members import TeamMember


class TeamMemberRepository(ITeamMemberRepository):
    def get_multiple_by_teams(self, teams):
        """
        Get list members of multiple teams
        :param teams:
        :return:
        """
        return TeamMember.objects.filter(team__in=teams)
