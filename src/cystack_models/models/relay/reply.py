from django.db import models

from shared.utils.app import now


class Reply(models.Model):
    lookup = models.CharField(max_length=255, blank=False, db_index=True)
    encrypted_metadata = models.TextField(blank=False)
    created_at = models.FloatField()

    class Meta:
        db_table = 'cs_reply'

    @classmethod
    def create(cls, lookup, encrypted_metadata):
        new_reply = cls(lookup=lookup, encrypted_metadata=encrypted_metadata, created_at=now(return_float=True))
        new_reply.save()
        return new_reply
