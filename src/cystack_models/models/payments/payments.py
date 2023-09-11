import ast
from datetime import datetime

from django.db import models
from django.conf import settings
from django.db.models import F

from shared.constants.transactions import *
from shared.utils.app import now
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
    mobile_invoice_id = models.CharField(max_length=128, null=True)
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
    enterprise_id = models.CharField(max_length=128, null=True, default=None)

    class Meta:
        db_table = 'cs_payments'
        indexes = [
            models.Index(fields=['created_time', ]),
            models.Index(fields=['status', ]),
        ]

    @classmethod
    def create(cls, **data):
        user = data["user"]
        scope = data.get("scope", settings.SCOPE_PWD_MANAGER)
        plan = data.get("plan")
        description = data.get("description")
        payment_method = data.get("payment_method", PAYMENT_METHOD_CARD)
        stripe_invoice_id = data.get("stripe_invoice_id", None)
        mobile_invoice_id = data.get("mobile_invoice_id", None)
        duration = data.get("duration", DURATION_MONTHLY)
        status = data.get("status", PAYMENT_STATUS_PENDING)
        currency = data.get('currency')
        total_price = data.get("total_price")
        metadata = data.get("metadata", "")
        enterprise_id = data.get("enterprise_id")
        if metadata and isinstance(metadata, dict):
            enterprise_id = metadata.get("enterprise_id") or enterprise_id
            metadata.pop("promo_code", None)
            metadata = str(metadata)
        new_payment = cls(
            user=user, scope=scope, description=description, duration=duration, created_time=now(), plan=plan,
            payment_method=payment_method, stripe_invoice_id=stripe_invoice_id, mobile_invoice_id=mobile_invoice_id,
            status=status,
            currency=currency, metadata=metadata, enterprise_id=enterprise_id
        )
        new_payment.save()
        new_payment.payment_id = "{}{}".format(BANKING_ID_PWD_MANAGER, 10000 + new_payment.id)
        new_payment.save()

        # Set promo code and customer
        promo_code = data.get("promo_code", None)
        new_payment.set_promo_code(promo_code=promo_code)
        customer = data.get('customer', None)
        new_payment.set_customer(customer=customer)

        # Create payment items
        new_payment.set_payment_items(**data)

        if total_price is None:
            new_payment.set_total_price()
        else:
            new_payment.total_price = total_price
            new_payment.save()

        # Set banking code
        if new_payment.payment_method == PAYMENT_METHOD_BANKING:
            if scope == settings.SCOPE_PWD_MANAGER:
                new_payment.code = "{}{}".format(BANKING_ID_PWD_MANAGER, 10000 + new_payment.id)
            else:
                new_payment.code = "{}{}".format(BANKING_ID_WEB_SECURITY, 10000 + new_payment.id)
            new_payment.bank_id = data.get("bank_id")
            new_payment.save()

        return new_payment

    @classmethod
    def get_duration_month_number(cls, duration):
        if duration == DURATION_YEARLY:
            return 12
        elif duration == DURATION_HALF_YEARLY:
            return 6
        return 1

    def set_promo_code(self, promo_code=None):
        """
        Set promo code for this payment
        :param promo_code: Code
        :return:
        """
        if promo_code is None:
            self.promo_code = None
        else:
            try:
                promo_obj = PromoCode.objects.get(id=promo_code)
                self.promo_code = promo_obj
                promo_obj.remaining_times = F('remaining_times') - 1
                promo_obj.save()
            except PromoCode.DoesNotExist:
                self.promo_code = None
        self.save()

    def set_customer(self, customer=None):
        """
        Set customer for this payment
        :param customer:
        :return:
        """
        if customer is None:
            self.customer = None
        else:
            new_customer = Customer.create(**customer)
            self.customer = new_customer
        self.save()

    def get_customer_dict(self):
        if not self.customer:
            return {}
        return {
            "full_name": self.customer.full_name,
            "organization": self.customer.organization,
            "address": self.customer.address,
            "city": self.customer.city,
            "state": self.customer.state,
            "postal_code": self.customer.postal_code,
            "phone_number": self.customer.phone_number,
            "last4": self.customer.last4,
            "brand": self.customer.brand,
            "country": "" if not self.customer.country else self.customer.country.country_name
        }

    def set_payment_items(self, **data):
        payments_items = data.get("payment_items", [])
        self.payment_items.model.create_multiple(self, *payments_items)

    def set_total_price(self):
        from cystack_models.models.user_plans.pm_plans import PMPlan

        # Get total price without discount
        number = int(self.get_metadata().get("number_members", 1))
        plan_price = PMPlan.objects.get(alias=self.plan).get_price(duration=self.duration, currency=self.currency)
        self.total_price = plan_price * number

        # Get discount here
        if self.promo_code is not None:
            self.discount = self.promo_code.get_discount(self.total_price, duration=self.duration)
        # Finally, calc total price
        self.total_price = max(round(self.total_price - self.discount, 2), 0)
        self.save()

    def get_metadata(self):
        if not self.metadata:
            return {}
        return ast.literal_eval(str(self.metadata))

    def get_created_time_str(self):
        return datetime.utcfromtimestamp(self.created_time).strftime('%H:%M:%S %d-%m-%Y')