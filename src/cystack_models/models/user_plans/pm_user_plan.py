import stripe

from django.db import models

from shared.constants.transactions import *
from shared.utils.app import now
from cystack_models.interfaces.user_plans.user_plan import UserPlan
from cystack_models.models.user_plans.pm_plans import PMPlan
from cystack_models.models.payments.promo_codes import PromoCode
from cystack_models.models.users.users import User


class PMUserPlan(UserPlan):
    user = models.OneToOneField(
        User, to_field='user_id', primary_key=True, related_name="pm_user_plan", on_delete=models.CASCADE
    )
    ref_plan_code = models.CharField(max_length=128, null=True, default=None)
    number_members = models.IntegerField(default=1)  # Number of member business
    pm_stripe_subscription = models.CharField(max_length=255, null=True)
    pm_stripe_subscription_created_time = models.IntegerField(null=True)

    pm_plan = models.ForeignKey(PMPlan, on_delete=models.CASCADE, related_name="pm_user_plan")
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, related_name="pm_user_plans", null=True, default=None
    )

    class Meta:
        db_table = 'cs_pm_user_plan'

    @classmethod
    def update_or_create(cls, user, pm_plan_alias=PLAN_TYPE_PM_FREE, duration=DURATION_MONTHLY):
        """
        Create plan object
        :param user: (obj) User object
        :param pm_plan_alias: (str) PM plan alias
        :param duration: (str) duration of this plan
        :return:
        """
        plan_type = PMPlan.objects.get(alias=pm_plan_alias)
        try:
            user_plan = cls.objects.get(user=user)
            user_plan.pm_plan = plan_type
            user_plan.duration = duration
            user_plan.save()
        except cls.DoesNotExist:
            user_plan = cls(pm_plan=plan_type, user=user, duration=duration)
            user_plan.save()
        return user_plan

    def get_plan_type_alias(self) -> str:
        return self.pm_plan.get_alias()

    def get_plan_type_name(self) -> str:
        return self.pm_plan.get_name()

    def is_subscription(self):
        stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            return True if stripe_subscription.cancel_at_period_end is False else False
        if self.start_period and self.end_period and self.end_period >= now():
            return True
        return False

    def is_cancel_at_period_end(self) -> bool:
        stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            return stripe_subscription.cancel_at_period_end
        return self.cancel_at_period_end

    def get_subscription(self):
        """
        Get subscription object of this plan
        :return:
        """
        stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            return True if stripe_subscription.cancel_at_period_end is False else False
        if self.start_period and self.end_period and self.end_period >= now():
            return True
        return False

    def get_stripe_subscription(self):
        """
        Get Stripe Subscription object
        :return:
        """
        if not self.pm_stripe_subscription:
            return None
        return stripe.Subscription.retrieve(self.pm_stripe_subscription)

    def cancel_stripe_subscription(self):
        """
        Cancel Stripe subscription
        :return:
        """
        self.pm_stripe_subscription = None
        self.pm_stripe_subscription_created_time = None
        self.promo_code = None
        self.save()

    def get_next_billing_time(self, duration=None):
        """
        Get next billing time of this plan
        :param duration:
        :return:
        """
        # If subscription object is None => Get next billing time of this user plan
        stripe_subscription = self.get_stripe_subscription()
        if not stripe_subscription:
            # If user subscribed a plan
            if self.end_period:
                return self.end_period
            # User is not still subscribe any subscription
            return now() #+ Payment.get_duration_month_number(duration=duration) * 30 * 86400
        else:
            if stripe_subscription.status == "trialing":
                return stripe_subscription.trial_end
            return stripe_subscription.current_period_end

    def get_current_number_members(self):
        return self.number_members

    def get_max_allow_members(self):
        if self.get_plan_type_alias() == PLAN_TYPE_PM_ENTERPRISE:
            return self.number_members
        return self.pm_plan.get_max_number_members()

    def set_default_payment_method(self, method):
        self.default_payment_method = method
        self.save()

    def get_default_payment_method(self):
        return self.default_payment_method

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
