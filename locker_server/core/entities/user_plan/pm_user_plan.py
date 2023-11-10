from typing import Union

import stripe

from locker_server.core.entities.payment.promo_code import PromoCode
from locker_server.core.entities.user.user import User
from locker_server.core.entities.user_plan.pm_plan import PMPlan
from locker_server.shared.constants.transactions import DURATION_MONTHLY, PAYMENT_METHOD_CARD, DURATION_YEARLY, \
    DURATION_HALF_YEARLY, PLAN_TYPE_PM_FREE, PAYMENT_STATUS_PAST_DUE
from locker_server.shared.utils.app import now


class PMUserPlan(object):
    def __init__(self, pm_user_plan_id: int, user: User, duration: str = DURATION_MONTHLY, start_period: float = None,
                 end_period: float = None, cancel_at_period_end: bool = False, custom_endtime: float = None,
                 default_payment_method: str = PAYMENT_METHOD_CARD, ref_plan_code: str = None, number_members: int = 1,
                 personal_trial_applied: bool = False, enterprise_trial_applied: bool = False,
                 personal_trial_mobile_applied: bool = False, personal_trial_web_applied: bool = False,
                 pm_stripe_subscription: str = None, pm_stripe_subscription_created_time: int = None,
                 pm_mobile_subscription: str = None, extra_time: int = 0, extra_plan: str = None,
                 member_billing_updated_time: float = None, attempts: int = 0, pm_plan: PMPlan = None,
                 promo_code: PromoCode = None):
        self._pm_user_plan_id = pm_user_plan_id
        self._user = user
        self._duration = duration
        self._start_period = start_period
        self._end_period = end_period
        self._cancel_at_period_end = cancel_at_period_end
        self._custom_endtime = custom_endtime
        self._default_payment_method = default_payment_method
        self._ref_plan_code = ref_plan_code
        self._number_members = number_members
        self._personal_trial_applied = personal_trial_applied
        self._enterprise_trial_applied = enterprise_trial_applied
        self._personal_trial_mobile_applied = personal_trial_mobile_applied
        self._personal_trial_web_applied = personal_trial_web_applied
        self._pm_stripe_subscription = pm_stripe_subscription
        self._pm_stripe_subscription_created_time = pm_stripe_subscription_created_time
        self._pm_mobile_subscription = pm_mobile_subscription
        self._extra_time = extra_time
        self._extra_plan = extra_plan
        self._member_billing_updated_time = member_billing_updated_time
        self._attempts = attempts
        self._pm_plan = pm_plan
        self._promo_code = promo_code

    @property
    def pm_user_plan_id(self):
        return self._pm_user_plan_id

    @property
    def user(self):
        return self._user

    @property
    def duration(self):
        return self._duration

    @property
    def start_period(self):
        return self._start_period

    @property
    def end_period(self):
        return self._end_period

    @property
    def cancel_at_period_end(self):
        return self._cancel_at_period_end

    @property
    def custom_endtime(self):
        return self._custom_endtime

    @property
    def default_payment_method(self):
        return self._default_payment_method

    @property
    def ref_plan_code(self):
        return self._ref_plan_code

    @property
    def number_members(self):
        return self._number_members

    @property
    def personal_trial_applied(self):
        return self._personal_trial_applied

    @property
    def enterprise_trial_applied(self):
        return self._enterprise_trial_applied

    @property
    def personal_trial_mobile_applied(self):
        return self._personal_trial_mobile_applied

    @property
    def personal_trial_web_applied(self):
        return self._personal_trial_web_applied

    @property
    def pm_stripe_subscription(self):
        return self._pm_stripe_subscription

    @property
    def pm_stripe_subscription_created_time(self):
        return self._pm_stripe_subscription_created_time

    @property
    def pm_mobile_subscription(self):
        return self._pm_mobile_subscription

    @property
    def extra_time(self):
        return self._extra_time

    @property
    def extra_plan(self):
        return self._extra_plan

    @property
    def member_billing_updated_time(self):
        return self._member_billing_updated_time

    @property
    def attempts(self):
        return self._attempts

    @property
    def pm_plan(self):
        return self._pm_plan

    @property
    def promo_code(self):
        return self._promo_code

    @classmethod
    def get_duration_month_number(cls, duration):
        if duration == DURATION_YEARLY:
            return 12
        elif duration == DURATION_HALF_YEARLY:
            return 6
        return 1

    def is_personal_trial_applied(self) -> bool:
        return self.personal_trial_applied

    def get_stripe_subscription(self):
        if not self.pm_stripe_subscription:
            return None
        return stripe.Subscription.retrieve(self.pm_stripe_subscription)

    def get_plan_type_alias(self) -> str:
        return self.pm_plan.alias

    def get_next_billing_time(self, duration: str = None) -> Union[float, int]:
        if self.pm_plan.alias in [PLAN_TYPE_PM_FREE]:
            return None
        stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            if stripe_subscription.status == "trialing":
                return stripe_subscription.trial_end
            return stripe_subscription.current_period_end
        # If user subscribed a plan
        if self.end_period:
            return self.end_period
        # User is not still subscribe any subscription
        return now() + PMUserPlan.get_duration_month_number(duration=duration) * 30 * 86400

    def is_subscription(self) -> bool:
        stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            return True if stripe_subscription.cancel_at_period_end is False else False
        if self.start_period and self.end_period and self.end_period >= now():
            return True
        return False

    def is_trialing(self):
        stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            return stripe_subscription.status == "trialing"
        mobile_subscription = self.pm_mobile_subscription
        return self.start_period and self.end_period and self.personal_trial_applied and mobile_subscription is None

    def is_cancel_at_period_end(self) -> bool:
        stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            return stripe_subscription.cancel_at_period_end
        return self.cancel_at_period_end

    def get_default_payment_method(self):
        return self.default_payment_method

    def get_max_allow_members(self):
        if self.pm_plan.is_team_plan:
            return self.number_members
        return self.pm_plan.max_number

    @staticmethod
    def get_next_attempts_duration(current_number_attempts):
        if current_number_attempts < 2:
            return 86400
        return 86400 * 3

    @classmethod
    def get_next_attempts_day_str(cls, current_number_attempts):
        if current_number_attempts < 2:
            return "1 day from today"
        return "3 days from today"

    def get_next_retry_payment_date(self, stripe_subscription=None):
        if self.get_plan_type_alias() in [PLAN_TYPE_PM_FREE]:
            return None
        # Retrieve Stripe subscription object
        if not stripe_subscription:
            stripe_subscription = self.get_stripe_subscription()
        if stripe_subscription:
            if stripe_subscription.status not in [PAYMENT_STATUS_PAST_DUE]:
                return None
            latest_invoice = stripe_subscription.latest_invoice
            if not latest_invoice:
                return None
            latest_invoice_obj = stripe.Invoice.retrieve(latest_invoice)
            return latest_invoice_obj.next_payment_attempt
        if self.attempts > 0:
            return PMUserPlan.get_next_attempts_duration(
                current_number_attempts=self.attempts
            ) + self.end_period
