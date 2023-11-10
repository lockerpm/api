import uuid

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.utils.app import now


class AbstractEnterpriseGroupORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.CharField(max_length=128)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    created_by = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.SET_NULL, related_name="created_enterprise_groups",
        null=True
    )
    enterprise = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_MODEL, on_delete=models.CASCADE, related_name="groups"
    )

    class Meta:
        abstract = True

    @classmethod
    def create(cls, enterprise, name: str, created_by=None):
        new_group = cls(
            name=name, enterprise=enterprise, creation_date=now(), revision_date=now(), created_by=created_by
        )
        new_group.save()
        return new_group

