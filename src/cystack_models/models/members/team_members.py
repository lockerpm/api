import uuid
from typing import Dict

from django.db import models

from shared.utils.app import now
from shared.constants.members import *
from cystack_models.models.users.users import User
from cystack_models.models.teams.teams import Team
from cystack_models.models.members.member_roles import MemberRole


class TeamMember(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    external_id = models.CharField(max_length=300, null=True)
    access_time = models.IntegerField()
    is_default = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)

    key = models.TextField(null=True)
    reset_password_key = models.TextField(null=True)
    status = models.CharField(max_length=128, default=PM_MEMBER_STATUS_CONFIRMED)
    email = models.CharField(max_length=128, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_members", null=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_members")
    role = models.ForeignKey(MemberRole, on_delete=models.CASCADE, related_name="team_members")

    class Meta:
        db_table = 'cs_team_members'
        unique_together = ('user', 'team', 'role')

    @classmethod
    def create_multiple(cls, team: Team, *members: [Dict]):
        """
        Create multiple members of the team
        :param team: (Team) Team object
        :param members: (list) Members data
        :return:
        """
        for member in members:
            try:
                cls.create(
                    team=team,
                    user=member["user"],
                    role_id=member["role"].name,
                    is_primary=member.get("is_primary", False),
                    is_default=member.get("is_default", False),
                )
            except:
                continue

    @classmethod
    def create(cls, team: Team, user: User, role_id: str, is_primary=False, is_default=False,
               status=PM_MEMBER_STATUS_CONFIRMED):
        new_member = TeamMember.objects.create(
            user=user, role_id=role_id, team=team, access_time=now(),
            is_primary=is_primary,
            is_default=is_default,
            status=status
        )
        return new_member

    @classmethod
    def create_with_collections(cls, team: Team, user: User, role_id: str, is_primary=False, is_default=False,
                                status=PM_MEMBER_STATUS_CONFIRMED,  *collection_ids):
        new_member = cls.create(team, user, role_id, is_primary, is_default, status)
        new_member.collections_members.model.create_multiple(new_member, *collection_ids)
        return new_member
