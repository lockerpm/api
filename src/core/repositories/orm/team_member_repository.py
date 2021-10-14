import jwt

from django.conf import settings

from core.repositories import ITeamMemberRepository
from shared.constants.members import *
from shared.constants.token import TOKEN_EXPIRED_TIME_INVITE_MEMBER, TOKEN_TYPE_INVITE_MEMBER, TOKEN_PREFIX
from shared.utils.app import now
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

    def create_invitation_token(self, member: TeamMember) -> str:
        created_time = now()
        expired_time = created_time + TOKEN_EXPIRED_TIME_INVITE_MEMBER * 3600
        payload = {
            "scope": settings.SCOPE_PWD_MANAGER,
            "member": member.email,
            "team": member.team.id,
            "created_time": created_time,
            "expired_time": expired_time,
            "token_type": TOKEN_TYPE_INVITE_MEMBER
        }
        token_value = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        token_value = TOKEN_PREFIX + token_value.decode('utf-8')
        member.token_invitation = token_value
        member.save()
        return token_value
