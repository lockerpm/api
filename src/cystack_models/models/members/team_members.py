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
    is_added_by_group = models.BooleanField(default=False)

    # Show/hide passwords when the team ciphers don't have any collections
    hide_passwords = models.BooleanField(default=False)

    key = models.TextField(null=True)
    reset_password_key = models.TextField(null=True)
    status = models.CharField(max_length=128, default=PM_MEMBER_STATUS_CONFIRMED)
    email = models.CharField(max_length=128, null=True)
    token_invitation = models.TextField(null=True, default=None)
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
    def create(cls, team: Team, role_id: str, is_primary=False, is_default=False,
               status=PM_MEMBER_STATUS_CONFIRMED, user: User = None, email: str = None):
        new_member = TeamMember.objects.create(
            user=user, email=email, role_id=role_id, team=team, access_time=now(),
            is_primary=is_primary,
            is_default=is_default,
            status=status
        )
        return new_member

    @classmethod
    def create_with_data(cls, team: Team, role_id: str, **data):
        new_member = TeamMember.objects.create(
            team=team, role_id=role_id, access_time=now(),
            user=data.get("user"),
            email=data.get("email"),
            is_primary=data.get("is_primary", False),
            is_default=data.get("is_default", False),
            is_added_by_group=data.get("is_added_by_group", False),
            status=data.get("status", PM_MEMBER_STATUS_CONFIRMED),
            key=data.get("key"),
            token_invitation=data.get("token_invitation")
        )
        if data.get("group_id"):
            new_member.groups_members.model.retrieve_or_create(data.get("group_id"), new_member.id)
        return new_member

    @classmethod
    def create_with_group(cls, team: Team, **data):
        group = data.get("group")
        role_id = group.role_id if group else (data.get("role_id") or data.get("role"))
        new_member = TeamMember.objects.create(
            team=team,
            role_id=role_id,
            access_time=now(),
            user=data.get("user"),
            email=data.get("email"),
            is_primary=data.get("is_primary", False),
            is_default=data.get("is_default", False),
            is_added_by_group=data.get("is_added_by_group", False),
            status=data.get("status", PM_MEMBER_STATUS_CONFIRMED),
            key=data.get("key"),
            token_invitation=data.get("token_invitation")
        )
        if group:
            new_member.groups_members.model.retrieve_or_create(group.id, new_member.id)
        return new_member

    @classmethod
    def create_with_collections(cls, team: Team, role_id: str, is_primary=False, is_default=False,
                                status=PM_MEMBER_STATUS_CONFIRMED, user: User = None, email: str = None,
                                collections: list = None):
        new_member = cls.create(team, role_id, is_primary, is_default, status, user, email)
        if collections:
            new_member.collections_members.model.create_multiple(new_member, *collections)
        return new_member
