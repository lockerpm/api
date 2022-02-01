import requests

from django.conf import settings

from shared.background import LockerBackgroundFactory, BG_NOTIFY
from core.settings import CORE_CONFIG
from shared.constants.transactions import *
from cystack_models.factory.payment_method.i_payment_method import IPaymentMethod
from cystack_models.models.payments.payments import Payment


PAYMENT_API = "{}/micro_services/cystack_platform/payments/wallet".format(settings.GATEWAY_API)

HEADERS = {
    'User-agent': 'CyStack Cloud Security',
    "Authorization": settings.MICRO_SERVICE_USER_AUTH
}


class WalletPaymentMethod(IPaymentMethod):
    def create_recurring_subscription(self, amount: float, plan_type: str, coupon=None,
                                      duration: str = DURATION_MONTHLY, **kwargs):
        pass

    def upgrade_recurring_subscription(self, amount: float, plan_type: str, coupon=None,
                                       duration: str = DURATION_MONTHLY, **kwargs):
        """
        Upgrade user's plan to new plan
        :param amount: (float) Money need pay
        :param plan_type: (str) Plan alias
        :param coupon: (obj) PromoCode object
        :param duration: (str) duration: monthly/half_yearly/yearly
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        payment_repository = CORE_CONFIG["repositories"]["IPaymentRepository"]()
        currency = kwargs.get("currency", CURRENCY_VND)
        # First, call to CyStack ID to pay
        payment_data = {
            "user_id": self.user.user_id,
            "currency": currency,
            "amount": amount,
            "scope": self.scope,
        }
        res = requests.post(url=PAYMENT_API, headers=HEADERS, json=payment_data, verify=False)
        if res.status_code == 400:
            return {"success": False, "error": res.json()}
        if res.status_code == 200:
            # Create invoice
            new_invoice = Payment.create(**{
                "user": self.user,
                "plan": plan_type,
                "description": "Upgrade plan",
                "payment_method": PAYMENT_METHOD_WALLET,
                "duration": duration,
                "currency": currency,
                "promo_code": coupon.id if coupon else None,
                "customer": user_repository.get_customer_data(user=self.user),
                "scope": self.scope,
                "metadata": kwargs
            })
            payment_repository.set_paid(payment=new_invoice)
            # Upgrade user plan
            user_repository.update_plan(
                user=self.user, plan_type_alias=plan_type, duration=duration, scope=self.scope, **kwargs
            )
            # Send mail
            LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="pay_successfully", **{"payment": new_invoice}
            )

            return {"success": True}
        return {"success": False}

    def cancel_recurring_subscription(self, **kwargs):
        """
        Cancel or continue subscription
        :return: End period if cancel plan. Return None if continue scan
        """
        current_plan = self.get_current_plan(**kwargs)
        current_plan.cancel_at_period_end = True if current_plan.cancel_at_period_end is False else False
        current_plan.save()
        if current_plan.cancel_at_period_end is True:
            return current_plan.end_period
        return None

    def cancel_immediately_recurring_subscription(self, **kwargs):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        # Downgrade user plan
        user_repository.update_plan(
            user=self.user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=self.scope
        )

    def recurring_subtract(self, amount: float, plan_type: str,
                           coupon=None, duration: str = DURATION_MONTHLY, **kwargs):
        return self.upgrade_recurring_subscription(
            amount=amount, plan_type=plan_type, coupon=coupon, duration=duration, **kwargs
        )

    def onetime_payment(self, amount: float, plan_type: str, coupon=None, **kwargs):
        """
        One-time payment
        :param amount: (float) Money
        :param plan_type: (str) Plan alias
        :param coupon: (obj) Promo code object
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """
