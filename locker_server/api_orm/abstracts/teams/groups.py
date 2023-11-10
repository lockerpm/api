from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.members import MEMBER_ROLE_MEMBER


class AbstractGroupORM(models.Model):
    id = models.AutoField(primary_key=True)
    access_all = models.BooleanField(default=True)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    team = models.ForeignKey(
        locker_server_settings.LS_TEAM_MODEL, on_delete=models.CASCADE, related_name="groups"
    )
    enterprise_group = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_GROUP_MODEL, on_delete=models.CASCADE,
        related_name="sharing_groups", null=True
    )
    role = models.ForeignKey(
        locker_server_settings.LS_MEMBER_ROLE_MODEL, on_delete=models.CASCADE,
        related_name="sharing_groups", default=MEMBER_ROLE_MEMBER
    )

    class Meta:
        abstract = True
        unique_together = ('team', 'enterprise_group')

    @classmethod
    def retrieve_or_create(cls, team_id, enterprise_group_id, **data):
        raise NotImplementedError

    @property
    def name(self):
        return self.enterprise_group.name if self.enterprise_group else None
