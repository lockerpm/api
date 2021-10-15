import uuid

from django.db import models

from cystack_models.models.users.users import User


class Folder(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.TextField(blank=True, null=True)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folders")

    class Meta:
        db_table = 'cs_folders'
