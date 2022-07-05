from django.db import models


class DeletedRelayAddress(models.Model):
    address_hash = models.CharField(max_length=64, db_index=True)
    num_forwarded = models.PositiveIntegerField(default=0)
    num_blocked = models.PositiveIntegerField(default=0)
    num_replied = models.PositiveIntegerField(default=0)
    num_spam = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'cs_deleted_relay_addresses'
