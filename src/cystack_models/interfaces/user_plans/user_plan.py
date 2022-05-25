from django.db import models

from shared.constants.transactions import DURATION_MONTHLY, PAYMENT_METHOD_CARD


class UserPlan(models.Model):
    duration = models.CharField(max_length=128, default=DURATION_MONTHLY)
    start_period = models.FloatField(null=True, default=None)
    end_period = models.FloatField(null=True, default=None)
    cancel_at_period_end = models.BooleanField(default=False)
    custom_endtime = models.FloatField(null=True, default=None)  # Custom endtime for some special cases
    default_payment_method = models.CharField(max_length=128, default=PAYMENT_METHOD_CARD)

    class Meta:
        abstract = True

    def get_plan_obj(self):
        raise NotImplementedError

    def get_plan_type_alias(self) -> str:
        raise NotImplementedError

    def get_plan_type_name(self) -> str:
        """
        Get plan type name
        :return:
        """

    def is_subscription(self):
        raise NotImplementedError

    def is_cancel_at_period_end(self) -> bool:
        raise NotImplementedError

    def get_subscription(self):
        """
        Get subscription object of this plan
        :return:
        """
        return self.get_stripe_subscription()

    def get_stripe_subscription(self):
        """
        Get Stripe Subscription object
        :return:
        """
        raise NotImplementedError

    def cancel_stripe_subscription(self):
        """
        Cancel Stripe subscription
        :return:
        """

    def cancel_mobile_subscription(self):
        """
        Cancel mobile subscription
        :return:
        """

    def get_next_billing_time(self, duration=None):
        """
        Get next billing time of this plan
        :param duration:
        :return:
        """
        raise NotImplementedError

    def calc_difference_price(self, new_plan, new_duration, currency):
        """
        Calc difference price when upgrade plan
        :param new_plan: (obj)
        :param new_duration: (str)
        :param currency: (str)
        :return:
        """

    def calc_update_price(self, new_plan, new_duration, new_quantity, currency, promo_code=None):
        """
        Calc amount when user update plan (via upgrade plan or change quantity)
        :param new_plan: (obj) Plan object
        :param new_duration: (str) New duration: monthly/half_yearly/yearly
        :param new_quantity: (int) New number of quantity
        :param currency: (str) Currency
        :param promo_code: (obj) Promo code object
        :return:
        """

    def is_personal_trial_applied(self) -> bool:
        pass
