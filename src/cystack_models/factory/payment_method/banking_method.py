from core.settings import CORE_CONFIG
from shared.constants.transactions import *
from cystack_models.factory.payment_method.i_payment_method import IPaymentMethod
from cystack_models.models.payments.payments import Payment


class BankingPaymentMethod(IPaymentMethod):
    def create_recurring_subscription(self, amount: float, plan_type: str, coupon=None,
                                      duration: str = DURATION_MONTHLY, **kwargs):
        pass

    def upgrade_recurring_subscription(self, amount: float, plan_type: str, coupon=None,
                                       duration: str = DURATION_MONTHLY, **kwargs):
        """
        Upgrade user's plan by create pending banking invoice
        :param amount: (float) Amount need pay
        :param plan_type: (str) Plan type alias/name....
        :param coupon: (obj) PromoCode object
        :param duration: (str) duration: monthly/half_yearly/yearly
        :param kwargs: (dict) Metadata: card, bank_id
        :return: New invoice
        """
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        currency = kwargs.get("currency", CURRENCY_VND)
        try:
            promo_code_str = coupon.id if coupon else None
        except AttributeError:
            promo_code_str = None
        new_invoice = Payment.create(**{
            "user": self.user,
            "plan": plan_type,
            "description": "Upgrade plan",
            "payment_method": PAYMENT_METHOD_BANKING,
            "duration": duration,
            "currency": currency,
            "promo_code": promo_code_str,
            "customer": user_repository.get_customer_data(user=self.user),
            "scope": self.scope,
            "bank_id": kwargs.get("bank_id"),
            "metadata": kwargs
        })
        return {"success": True, "banking_invoice": new_invoice}

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

    def recurring_subtract(self, amount: float, plan_type: str,
                           coupon=None, duration: str = DURATION_MONTHLY, **kwargs):
        pass

    def onetime_payment(self, amount: float, plan_type: str, coupon=None, **kwargs):
        pass
