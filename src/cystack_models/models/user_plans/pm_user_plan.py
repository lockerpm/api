import stripe

from django.conf import settings
from django.db import models

from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
from shared.constants.transactions import *
from shared.utils.app import now
from cystack_models.interfaces.user_plans.user_plan import UserPlan
from cystack_models.models.user_plans.pm_plans import PMPlan
from cystack_models.models.payments.promo_codes import PromoCode
from cystack_models.models.users.users import User
from cystack_models.models.payments.payments import Payment


class PMUserPlan(UserPlan):
    user = models.OneToOneField(
        User, to_field='user_id', primary_key=True, related_name="pm_user_plan", on_delete=models.CASCADE
    )
    ref_plan_code = models.CharField(max_length=128, null=True, default=None)
    number_members = models.IntegerField(default=1)  # Number of member business
    personal_trial_applied = models.BooleanField(default=False)     # Did this user apply the personal trial plan?
    pm_stripe_subscription = models.CharField(max_length=255, null=True)
    pm_stripe_subscription_created_time = models.IntegerField(null=True)
    pm_mobile_subscription = models.CharField(max_length=128, blank=True)

    pm_plan = models.ForeignKey(PMPlan, on_delete=models.CASCADE, related_name="pm_user_plan")
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, related_name="pm_user_plans", null=True, default=None
    )

    class Meta:
        db_table = 'cs_pm_user_plan'
        indexes = [
            models.Index(fields=['pm_mobile_subscription', ]),
        ]

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

    def get_plan_obj(self):
        return self.pm_plan

    def get_plan_type_alias(self) -> str:
        return self.get_plan_obj().get_alias()

    def get_plan_type_name(self) -> str:
        return self.get_plan_obj().get_name()

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

    def cancel_mobile_subscription(self):
        self.pm_mobile_subscription = None
        self.promo_code = None
        self.save()

    def get_next_billing_time(self, duration=None):
        """
        Get next billing time of this plan
        :param duration:
        :return:
        """
        # if this plan is not subscription plan => Return None
        if self.get_plan_type_alias() in [PLAN_TYPE_PM_FREE]:
            return None
        # If subscription object is None => Get next billing time of this user plan
        stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            if stripe_subscription.status == "trialing":
                return stripe_subscription.trial_end
            return stripe_subscription.current_period_end

        # If user subscribed a plan
        if self.end_period:
            return self.end_period
        # User is not still subscribe any subscription
        return now() + Payment.get_duration_month_number(duration=duration) * 30 * 86400

    def get_current_number_members(self):
        return self.number_members

    def get_max_allow_members(self):
        plan_obj = self.get_plan_obj()
        if plan_obj.is_team_plan:
            return self.number_members
        return plan_obj.get_max_number_members()

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
        :param promo_code: (str) Promo code string value
        :return:
        """
        current_time = now()
        # Get new plan price
        new_plan_price = new_plan.get_price(duration=new_duration, currency=currency)
        # Number of month duration billing by new duration
        duration_next_billing_month = Payment.get_duration_month_number(new_duration)
        # Calc discount
        error_promo = None
        promo_code_obj = None
        promo_description_en = None
        promo_description_vi = None
        if promo_code is not None and promo_code != "":
            promo_code_obj = PromoCode.check_valid(value=promo_code, current_user=self.user)
            if not promo_code_obj:
                error_promo = {"promo_code": ["This coupon is expired or incorrect"]}
            else:
                # if not (new_duration == DURATION_YEARLY and promo_code_obj.duration < 12):
                #     duration_next_billing_month = promo_code_obj.duration
                promo_description_en = promo_code_obj.description_en
                promo_description_vi = promo_code_obj.description_vi

        # If user subscribes by Stripe => Using Stripe service
        if self.pm_stripe_subscription:
            total_amount, next_billing_time = PaymentMethodFactory.get_method(
                user=self.user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
            ).calc_update_total_amount(new_plan=new_plan, new_duration=new_duration, new_quantity=new_quantity)
        # Else, calc manually
        else:
            # Calc immediate amount and next billing time
            # If this is the first time user register subscription
            if not self.end_period or not self.start_period:
                # Diff_price is price of the plan that user will subscribe
                total_amount = new_plan_price * new_quantity
                next_billing_time = self.get_next_billing_time(duration=new_duration)
            # Else, update the existed subscription
            else:
                # Calc old amount with discount
                old_price = self.pm_plan.get_price(duration=self.duration, currency=currency)
                old_amount = old_price * self.number_members
                if self.promo_code:
                    discount = self.promo_code.get_discount(old_amount, duration=self.duration)
                    old_amount = old_amount - discount
                # If new plan has same duration, next billing time does not change
                # Money used: (now - start) / (end - start) * old_price
                # Money remain: old_price - money_used
                # => Diff price: new_price - money_remain
                if self.duration == new_duration:
                    old_remain = old_amount * (
                            1 - (current_time - self.start_period) / (self.end_period - self.start_period)
                    )
                    new_remain = new_plan_price * new_quantity * (
                            (self.end_period - current_time) / (self.end_period - self.start_period)
                    )
                    total_amount = new_remain - old_remain
                    next_billing_time = self.get_next_billing_time(duration=new_duration)
                # Else, new plan has difference duration, the start of plan will be restarted
                else:
                    old_used = old_amount * (
                            (current_time - self.start_period) / (self.end_period - self.start_period)
                    )
                    old_remain = old_amount - old_used
                    total_amount = new_plan_price * new_quantity - old_remain
                    next_billing_time = current_time + duration_next_billing_month * 30 * 86400

        # Discount and immediate payment
        total_amount = max(total_amount, 0)
        discount = promo_code_obj.get_discount(total_amount, duration=new_duration) if promo_code_obj else 0.0
        immediate_amount = max(round(total_amount - discount, 2), 0)
        # Return result
        result = {
            "alias": new_plan.get_alias(),
            "price": round(new_plan_price, 2),
            "total_price": total_amount,
            "discount": discount,
            "duration": new_duration,
            "currency": currency,
            "immediate_payment": immediate_amount,
            "next_billing_time": next_billing_time,
            "promo_description": {
                "en": promo_description_en,
                "vi": promo_description_vi
            },
            "error_promo": error_promo
        }
        return result

    def calc_current_payment_price(self, currency):
        plan_price = self.pm_plan.get_price(duration=self.duration, currency=currency)
        total_price = plan_price * self.number_members
        # Calc discount
        discount = 0.0
        if self.promo_code is not None:
            # If the promo code of this plan is still available
            if self.user.payments.filter(promo_code=self.promo_code).count() < self.promo_code.duration:
                discount = self.promo_code.get_discount(total_price, duration=self.duration)
            # Else, remove promo code
            else:
                self.promo_code = None
                self.save()

        current_amount = max(round(total_price - discount, 2), 0)
        return current_amount

    def is_personal_trial_applied(self) -> bool:
        return self.personal_trial_applied
