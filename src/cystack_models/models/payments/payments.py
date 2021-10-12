import ast

from django.db import models
from django.conf import settings

from shared.constants.transactions import *
from cystack_models.models.users.users import User
from cystack_models.models.payments.customers import Customer
from cystack_models.models.payments.promo_codes import PromoCode


class Payment(models.Model):
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
    code = models.CharField(max_length=128, null=True)
    bank_id = models.IntegerField(null=True, default=None)

    scope = models.CharField(max_length=255, default=settings.SCOPE_PWD_MANAGER)
    plan = models.CharField(max_length=255)
    duration = models.CharField(max_length=16, default=DURATION_MONTHLY)
    metadata = models.TextField(blank=True, default="")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, related_name="payments", null=True)
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, related_name="payments", null=True, default=None
    )

    class Meta:
        db_table = 'cs_payments'

    def get_metadata(self):
        if not self.metadata:
            return {}
        return ast.literal_eval(str(self.metadata))
