import uuid

from django.db import models

from cystack_models.models.enterprises.enterprises import Enterprise
from shared.utils.app import now


class EnterpriseGroup(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.CharField(max_length=128)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="groups")

    class Meta:
        db_table = 'e_enterprise_groups'

    @classmethod
    def create(cls, enterprise: Enterprise, name: str):
        new_group = cls(name=name, enterprise=enterprise, creation_date=now(), revision_date=now())
        new_group.save()
        return new_group
