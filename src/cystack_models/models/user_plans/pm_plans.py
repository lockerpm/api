from django.db import models


from shared.constants.transactions import DURATION_MONTHLY, DURATION_YEARLY, DURATION_HALF_YEARLY, \
    CURRENCY_USD, CURRENCY_VND
from shared.constants.ciphers import *
from cystack_models.models.user_plans.plan_types import PlanType


class PMPlan(models.Model):
    id = models.AutoField(primary_key=True)
    alias = models.CharField(max_length=128, blank=True, default="")
    name = models.CharField(max_length=128)

    # Price monthly
    price_usd = models.FloatField()
    price_vnd = models.FloatField()
    # Half-yearly price
    half_yearly_price_usd = models.FloatField(default=0)
    half_yearly_price_vnd = models.FloatField(default=0)
    # Price yearly
    yearly_price_usd = models.FloatField(default=0)
    yearly_price_vnd = models.FloatField(default=0)

    sync_device = models.IntegerField(null=True, default=None)
    limit_password = models.IntegerField(null=True, default=None)
    limit_secure_note = models.IntegerField(null=True, default=None)
    limit_identity = models.IntegerField(null=True, default=None)
    limit_payment_card = models.IntegerField(null=True, default=None)
    limit_crypto_asset = models.IntegerField(null=True, default=None)
    tools_password_reuse = models.BooleanField(default=False)
    tools_master_password_check = models.BooleanField(default=False)
    tools_data_breach = models.BooleanField(default=False)
    emergency_access = models.BooleanField(default=False)

    is_team_plan = models.BooleanField(default=False)
    max_number = models.IntegerField(null=True, default=None)
    team_dashboard = models.BooleanField(default=False)
    team_policy = models.BooleanField(default=False)
    team_prevent_password = models.BooleanField(default=False)
    team_activity_log = models.BooleanField(default=False)

    plan_type = models.ForeignKey(PlanType, on_delete=models.CASCADE, related_name="pm_plans")

    class Meta:
        db_table = 'cs_pm_plans'

    def get_alias(self):
        return self.alias

    def get_name(self):
        return self.name

    def get_price_usd(self, duration=DURATION_MONTHLY):
        if duration == DURATION_YEARLY:
            return self.yearly_price_usd
        elif duration == DURATION_HALF_YEARLY:
            return self.half_yearly_price_usd
        return self.price_usd

    def get_price_vnd(self, duration=DURATION_MONTHLY):
        if duration == DURATION_YEARLY:
            return self.yearly_price_vnd
        elif duration == DURATION_HALF_YEARLY:
            return self.half_yearly_price_vnd
        return self.price_vnd

    def get_price(self, duration=DURATION_MONTHLY, currency=CURRENCY_USD):
        if currency == CURRENCY_VND:
            return self.get_price_vnd(duration)
        return self.get_price_usd(duration)

    def get_max_number_members(self):
        return self.max_number

    def get_sync_device(self):
        return self.sync_device

    def get_limit_password(self):
        return self.limit_password

    def get_limit_secure_note(self):
        return self.limit_secure_note

    def get_limit_identity(self):
        return self.limit_identity

    def get_limit_payment_card(self):
        return self.limit_payment_card

    def get_limit_totp(self):
        return None

    def get_limit_crypto_asset(self):
        return self.limit_crypto_asset

    def get_limit_ciphers_by_type(self, vault_type):
        if vault_type == CIPHER_TYPE_LOGIN:
            return self.get_limit_password()
        elif vault_type == CIPHER_TYPE_NOTE:
            return self.get_limit_secure_note()
        elif vault_type == CIPHER_TYPE_IDENTITY:
            return self.get_limit_identity()
        elif vault_type == CIPHER_TYPE_CARD:
            return self.get_limit_payment_card()
        elif vault_type == CIPHER_TYPE_TOTP:
            return self.get_limit_totp()
        elif vault_type == CIPHER_TYPE_CRYPTO:
            return self.get_limit_crypto_asset()

    def allow_tools_password_reuse(self):
        return self.tools_password_reuse

    def allow_tools_master_password_check(self):
        return self.tools_master_password_check

    def allow_tools_data_breach(self):
        return self.tools_data_breach

    def allow_emergency_access(self):
        return self.emergency_access

    def allow_team_dashboard(self):
        return self.team_dashboard

    def allow_team_policy(self):
        return self.team_policy

    def allow_team_prevent_password(self):
        return self.team_prevent_password

    def allow_team_activity_log(self):
        return self.team_activity_log
