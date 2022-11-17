from django.db import models

from shared.constants.members import MEMBER_ROLE_MEMBER
from shared.utils.app import now
from cystack_models.models.teams.teams import Team
from cystack_models.models.members.member_roles import MemberRole
from cystack_models.models.enterprises.groups.groups import EnterpriseGroup


class Group(models.Model):
    id = models.AutoField(primary_key=True)
    access_all = models.BooleanField(default=True)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="groups")
    enterprise_group = models.ForeignKey(
        EnterpriseGroup, on_delete=models.CASCADE, related_name="sharing_groups", null=True
    )
    role = models.ForeignKey(
        MemberRole, on_delete=models.CASCADE, related_name="sharing_groups", default=MEMBER_ROLE_MEMBER
    )

    class Meta:
        db_table = 'cs_groups'
        unique_together = ('team', 'enterprise_group')

    # @classmethod
    # def create(cls, team: Team, name: str, access_all: bool, collections: list):
    #     new_group = cls(
    #         team=team, name=name, access_all=access_all,
    #         creation_date=now(), revision_date=now()
    #     )
    #     new_group.save()
    #     return new_group

    @classmethod
    def retrieve_or_create(cls, team_id, enterprise_group_id, **data):
        group, is_created = cls.objects.get_or_create(
            team_id=team_id, enterprise_group_id=enterprise_group_id, defaults={
                "team_id": team_id,
                "enterprise_group_id": enterprise_group_id,
                "access_all": data.get("access_all", True),
                "creation_date": now(),
                "revision_date": now(),
                "role_id": data.get("role_id", MEMBER_ROLE_MEMBER)
            }
        )
        return group

    @property
    def name(self):
        return self.enterprise_group.name if self.enterprise_group else None
