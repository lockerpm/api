import uuid

from django.db import models

from locker_server.settings import locker_server_settings


class AbstractFolderORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.TextField(blank=True, null=True)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="folders"
    )

    class Meta:
        abstract = True
