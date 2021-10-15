from django.db import models


from shared.constants.transactions import DURATION_MONTHLY, DURATION_YEARLY, DURATION_HALF_YEARLY, \
    CURRENCY_USD, CURRENCY_VND
from cystack_models.models.user_plans.plan_types import PlanType


class PMPlan(models.Model):
    id = models.AutoField(primary_key=True)
    alias = models.CharField(max_length=128, blank=True, default="")
    name = models.CharField(max_length=128)
    max_number = models.IntegerField(null=True, default=None)
    max_device = models.IntegerField(null=True, default=None)
    max_device_type = models.IntegerField(null=True, default=None)
    # Price monthly
    price_usd = models.FloatField()
    price_vnd = models.FloatField()
    # Half-yearly price
    half_yearly_price_usd = models.FloatField(default=0)
    half_yearly_price_vnd = models.FloatField(default=0)
    # Price yearly
    yearly_price_usd = models.FloatField(default=0)
    yearly_price_vnd = models.FloatField(default=0)
    is_team_plan = models.BooleanField(default=False)
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
