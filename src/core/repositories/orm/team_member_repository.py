from core.repositories import ITeamMemberRepository

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

    def accept_invitation(self, member: TeamMember):
        """
        The user accepts the invitation of a team
        :param member: (obj) Member object represents for the invitation
        :return:
        """
        member.status = PM_MEMBER_STATUS_ACCEPTED
        member.email = None
        member.save()

    def reject_invitation(self, member: TeamMember):
        """
        This user rejects the invitation
        :param member: (ojb) Member object
        :return:
        """
        member.delete()
