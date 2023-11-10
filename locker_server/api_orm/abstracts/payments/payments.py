import ast
from datetime import datetime

from django.db import models
from django.conf import settings

from locker_server.shared.constants.transactions import CURRENCY_USD, TRANSACTION_TYPE_PAYMENT, DURATION_MONTHLY
from locker_server.settings import locker_server_settings




class AbstractPaymentORM(models.Model):
    id = models.AutoField(primary_key=True)
    payment_id = models.CharField(max_length=128, null=True, default=None)
    created_time = models.FloatField()
    total_price = models.FloatField(default=0)
    discount = models.FloatField(default=0)
    currency = models.CharField(max_length=8, default=CURRENCY_USD)
    status = models.CharField(max_length=64)
    description = models.CharField(max_length=255, default="", blank=True)
    transaction_type = models.CharField(max_length=128, default=TRANSACTION_TYPE_PAYMENT)
    payment_method = models.CharField(max_length=64, null=True)
    failure_reason = models.CharField(max_length=128, null=True, blank=True)
    stripe_invoice_id = models.CharField(max_length=128, null=True)
    mobile_invoice_id = models.CharField(max_length=128, null=True)
    code = models.CharField(max_length=128, null=True)
    bank_id = models.IntegerField(null=True, default=None)
    scope = models.CharField(max_length=255, default=settings.SCOPE_PWD_MANAGER)
    plan = models.CharField(max_length=255)
    duration = models.CharField(max_length=16, default=DURATION_MONTHLY)
    metadata = models.TextField(blank=True, default="")
    enterprise_id = models.CharField(max_length=128, null=True, default=None)
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    promo_code = models.ForeignKey(
        locker_server_settings.LS_PROMO_CODE_MODEL, on_delete=models.SET_NULL, related_name="payments",
        null=True, default=None
    )

    class Meta:
        abstract = True

    @classmethod
    def create(cls, **data):
        raise NotImplementedError

    # @classmethod
    # def get_duration_month_number(cls, duration):
    #     if duration == DURATION_YEARLY:
    #         return 12
    #     elif duration == DURATION_HALF_YEARLY:
    #         return 6
    #     return 1
    #

    def get_metadata(self):
        if not self.metadata:
            return {}
        return ast.literal_eval(str(self.metadata))

    def get_created_time_str(self):
        return datetime.utcfromtimestamp(self.created_time).strftime('%H:%M:%S %d-%m-%Y')