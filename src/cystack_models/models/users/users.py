from django.conf import settings
from django.db import models

from shared.constants.account import DEFAULT_KDF_ITERATIONS
from shared.constants.transactions import *


class User(models.Model):
    user_id = models.IntegerField(primary_key=True)
    created_time = models.FloatField()
    revision_time = models.FloatField(null=True)
    master_password = models.CharField(max_length=300)
    master_password_hint = models.CharField(max_length=128, blank=True, null=True, default="")
    master_password_score = models.FloatField(default=0)
    security_stamp = models.CharField(max_length=50, null=True)
    account_revision_date = models.FloatField(null=True)
    key = models.TextField(null=True)
    public_key = models.TextField(null=True)
    private_key = models.TextField(null=True)
    kdf = models.IntegerField(default=0)
    kdf_iterations = models.IntegerField(default=DEFAULT_KDF_ITERATIONS)
    timeout = models.IntegerField(default=15)
    timeout_action = models.CharField(default="lock", max_length=16)

    class Meta:
        db_table = 'cs_users'
        managed = False

    @classmethod
    def retrieve_or_create(cls, user_id):
        pass