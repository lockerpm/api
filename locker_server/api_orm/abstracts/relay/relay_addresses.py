import re
from hashlib import sha256

from django.db import models, transaction

from locker_server.settings import locker_server_settings


# class MaxRelayAddressReachedException(BaseException):
#     """
#     The max relay address is reached
#     """


class AbstractRelayAddressORM(models.Model):
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="relay_addresses"
    )
    address = models.CharField(max_length=64, unique=True)
    subdomain = models.ForeignKey(
        locker_server_settings.LS_RELAY_SUBDOMAIN_MODEL, on_delete=models.CASCADE, related_name="relay_addresses", null=True, default=None
    )
    domain = models.ForeignKey(
        locker_server_settings.LS_RELAY_DOMAIN_MODEL, on_delete=models.CASCADE, related_name="relay_addresses"
    )
    enabled = models.BooleanField(default=True)
    block_spam = models.BooleanField(default=False)
    description = models.CharField(max_length=64, blank=True)
    created_time = models.FloatField()
    updated_time = models.FloatField(null=True)
    num_forwarded = models.PositiveIntegerField(default=0)
    num_blocked = models.PositiveIntegerField(default=0)
    num_replied = models.PositiveIntegerField(default=0)
    num_spam = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    @classmethod
    def create(cls, user, **data):
        raise NotImplementedError
