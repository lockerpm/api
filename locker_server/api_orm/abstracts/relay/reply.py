from django.db import models

from locker_server.shared.utils.app import now


class AbstractReplyORM(models.Model):
    lookup = models.CharField(max_length=255, blank=False, db_index=True)
    encrypted_metadata = models.TextField(blank=False)
    created_at = models.FloatField()

    class Meta:
        abstract = True

