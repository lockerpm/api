from django.conf import settings
from django.db import models

from shared.constants.transactions import *
from shared.constants.members import *
from cystack_models.models.users.account_types import AccountType


class User(models.Model):
    user_id = models.IntegerField(primary_key=True)
    created_time = models.IntegerField()

    # stripe_customer_id = models.CharField(max_length=255, null=True)
    # stripe_subscription = models.CharField(max_length=128)
    # stripe_subscription_created_time = models.IntegerField(null=True)
    default_payment_method = models.CharField(max_length=128, default=PAYMENT_METHOD_WALLET)

    bw_id = models.CharField(max_length=128, null=True)  # Bitwarden User id
    bw_email = models.CharField(max_length=128, null=True)  # Bitwarden email: <user_id>@pw.cystack.org
    bw_email_verified = models.BooleanField(default=False)  # Bitwarden email verified?
    bw_public_key = models.CharField(max_length=512, null=True)  # Bitwarden user public key
    bw_master_pass_score = models.FloatField(null=True, default=0)
    bw_timeout = models.IntegerField(default=15)
    bw_timeout_action = models.CharField(default="lock", max_length=16)
    # account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True, default=ACCOUNT_TYPE_PERSONAL)

    class Meta:
        db_table = 'cs_users'
        managed = False
