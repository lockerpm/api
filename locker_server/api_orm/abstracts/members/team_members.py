import uuid

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.members import PM_MEMBER_STATUS_CONFIRMED
from locker_server.shared.utils.app import now


class AbstractTeamMemberORM(models.Model):
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
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="team_members", null=True
    )
    team = models.ForeignKey(
        locker_server_settings.LS_TEAM_MODEL, on_delete=models.CASCADE, related_name="team_members"
    )
    role = models.ForeignKey(
        locker_server_settings.LS_MEMBER_ROLE_MODEL, on_delete=models.CASCADE, related_name="team_members"
    )

    class Meta:
        abstract = True
        unique_together = ('user', 'team', 'role')

    @classmethod
    def create_multiple(cls, team_id: str, *members):
        for member in members:
            try:
                cls.create(
                    team_id=team_id,
                    user_id=member.get("user_id"),
                    role_id=member["role"].name,
                    is_primary=member.get("is_primary", False),
                    is_default=member.get("is_default", False),
                )
            except:
                continue

    @classmethod
    def create(cls, team_id: str, role_id: str, is_primary=False, is_default=False,
               status=PM_MEMBER_STATUS_CONFIRMED, user_id: int = None, email: str = None):
        raise NotImplementedError
    #
    # @classmethod
    # def create_with_data(cls, team: Team, role_id: str, **data):
    #     new_member = TeamMember.objects.create(
    #         team=team, role_id=role_id, access_time=now(),
    #         user=data.get("user"),
    #         email=data.get("email"),
    #         is_primary=data.get("is_primary", False),
    #         is_default=data.get("is_default", False),
    #         is_added_by_group=data.get("is_added_by_group", False),
    #         status=data.get("status", PM_MEMBER_STATUS_CONFIRMED),
    #         key=data.get("key"),
    #         token_invitation=data.get("token_invitation")
    #     )
    #     if data.get("group_id"):
    #         new_member.groups_members.model.retrieve_or_create(data.get("group_id"), new_member.id)
    #     return new_member
    #
    # @classmethod
    # def create_with_group(cls, team: Team, **data):
    #     group = data.get("group")
    #     role_id = group.role_id if group else (data.get("role_id") or data.get("role"))
    #     new_member = TeamMember.objects.create(
    #         team=team,
    #         role_id=role_id,
    #         access_time=now(),
    #         user=data.get("user"),
    #         email=data.get("email"),
    #         is_primary=data.get("is_primary", False),
    #         is_default=data.get("is_default", False),
    #         is_added_by_group=data.get("is_added_by_group", False),
    #         status=data.get("status", PM_MEMBER_STATUS_CONFIRMED),
    #         key=data.get("key"),
    #         token_invitation=data.get("token_invitation")
    #     )
    #     if group:
    #         new_member.groups_members.model.retrieve_or_create(group.id, new_member.id)
    #     return new_member
    #
    @classmethod
    def retrieve_or_create_with_group(cls, team_id: str, **data):
        group = data.get("group")
        role_id = group.role_id if group else (data.get("role_id") or data.get("role"))

        member_data = {
            "team_id": team_id,
            "role_id": role_id,
            "access_time": now(),
            "user_id": data.get("user_id"),
            "email": data.get("email"),
            "is_primary": data.get("is_primary", False),
            "is_default": data.get("is_default", False),
            "is_added_by_group": data.get("is_added_by_group", False),
            "status": data.get("status", PM_MEMBER_STATUS_CONFIRMED),
            "key": data.get("key"),
            "token_invitation": data.get("token_invitation")
        }
        if data.get("user_id"):
            member, is_created = cls.objects.get_or_create(
                team_id=team_id, user_id=data.get("user_id"), defaults=member_data
            )
        else:
            member, is_created = cls.objects.get_or_create(
                team_id=team_id, email=data.get("email"), defaults=member_data
            )
        if group:
            member.groups_members.model.retrieve_or_create(group.id, member.id)
        return member, is_created

    # @classmethod
    # def create_with_collections(cls, team: Team, role_id: str, is_primary=False, is_default=False,
    #                             status=PM_MEMBER_STATUS_CONFIRMED, user: User = None, email: str = None,
    #                             collections: list = None):
    #     new_member = cls.create(team, role_id, is_primary, is_default, status, user, email)
    #     if collections:
    #         new_member.collections_members.model.create_multiple(new_member, *collections)
    #     return new_member
