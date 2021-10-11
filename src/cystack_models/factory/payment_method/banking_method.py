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
            "customer": self.user.get_customer_data(),
            "scope": self.scope,
            "bank_id": kwargs.get("bank_id"),
            "metadata": kwargs
        })
        return {"success": True, "banking_invoice": new_invoice}

    def cancel_recurring_subscription(self, **kwargs):
        pass

    def recurring_subtract(self, amount: float, plan_type: str,
                           coupon=None, duration: str = DURATION_MONTHLY, **kwargs):
        pass

    def onetime_payment(self, amount: float, plan_type: str, coupon=None, **kwargs):
        pass
