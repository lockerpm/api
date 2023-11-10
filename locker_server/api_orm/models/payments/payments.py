from django.conf import settings
from django.db import models

from locker_server.api_orm.abstracts.payments.payments import AbstractPaymentORM
from locker_server.api_orm.models.payments.customers import CustomerORM
from locker_server.shared.constants.transactions import *
from locker_server.shared.utils.app import now


class PaymentORM(AbstractPaymentORM):
    customer = models.ForeignKey(CustomerORM, on_delete=models.SET_NULL, related_name="payments", null=True)

    class Meta(AbstractPaymentORM.Meta):
        swappable = 'LS_PAYMENT_MODEL'
        db_table = 'cs_payments'

    @classmethod
    def create(cls, **data):
        user_id = data["user_id"]
        scope = data.get("scope", settings.SCOPE_PWD_MANAGER)
        plan = data.get("plan")
        description = data.get("description")
        payment_method = data.get("payment_method", PAYMENT_METHOD_CARD)
        stripe_invoice_id = data.get("stripe_invoice_id", None)
        mobile_invoice_id = data.get("mobile_invoice_id", None)
        duration = data.get("duration", DURATION_MONTHLY)
        status = data.get("status", PAYMENT_STATUS_PENDING)
        currency = data.get('currency')

        metadata = data.get("metadata", "")
        enterprise_id = data.get("enterprise_id")
        if metadata and isinstance(metadata, dict):
            enterprise_id = metadata.get("enterprise_id") or enterprise_id
            metadata.pop("promo_code", None)
            metadata = str(metadata)
        new_payment_orm = cls(
            user_id=user_id, scope=scope, description=description, duration=duration, created_time=now(), plan=plan,
            payment_method=payment_method, stripe_invoice_id=stripe_invoice_id, mobile_invoice_id=mobile_invoice_id,
            status=status,
            currency=currency, metadata=metadata, enterprise_id=enterprise_id
        )
        new_payment_orm.save()
        new_payment_orm.payment_id = "{}{}".format(BANKING_ID_PWD_MANAGER, 10000 + new_payment_orm.id)
        new_payment_orm.save()

        return new_payment_orm
