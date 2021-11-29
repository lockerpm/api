import jwt

from django.conf import settings

from core.repositories import ITeamMemberRepository
from core.utils.account_revision_date import bump_account_revision_date
from shared.constants.members import *
from shared.constants.token import TOKEN_EXPIRED_TIME_INVITE_MEMBER, TOKEN_TYPE_INVITE_MEMBER, TOKEN_PREFIX
from shared.utils.app import now, diff_list
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

    def update_member(self, member: TeamMember, role_id: str, collections: list) -> TeamMember:
        # Update role
        member.role_id = role_id
        member.save()
        # Update member collections
        if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
            # Delete all groups of this member
            member.groups_members.all().delete()
            collections = []
        # Remove all old collections
        member.collections_members.all().delete()
        # Create member collections
        member.collections_members.model.create_multiple(member, *collections)
        # Bump revision date
        bump_account_revision_date(user=member.user)

        return member

    def get_list_groups(self, member: TeamMember):
        return member.groups_members.all().order_by('group_id')

    def update_list_groups(self, member: TeamMember, group_ids: list) -> TeamMember:
        role_id = member.role_id
        if role_id in [MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER]:
            group_ids = []
        existed_groups = list(self.get_list_groups(member).values_list('group_id', flat=True))
        removed_groups = diff_list(existed_groups, group_ids)
        member.groups_members.filter(group_id__in=removed_groups).delete()
        member.groups_members.model.create_multiple_by_member(member, *group_ids)
        # Bump account revision date
        bump_account_revision_date(team=member.team)
        return member
