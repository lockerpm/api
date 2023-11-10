from locker_server.core.entities.user_plan.pm_user_plan import PMUserPlan
from locker_server.shared.constants.transactions import DURATION_MONTHLY


class PaymentMethod:
    def __init__(self, user_plan: PMUserPlan, scope: str = None):
        self.user_plan = user_plan
        self.scope = scope

    def get_current_plan(self):
        return self.user_plan

    def create_recurring_subscription(self, amount: float, plan_type: str,
                                      coupon=None, duration: str = DURATION_MONTHLY, **kwargs):
        """
        Create new recurring subscription for user
        :param amount: (float) Money need pay
        :param plan_type: (str) Plan alias
        :param coupon: (obj) PromoCode object
        :param duration: (str) duration: monthly/half_yearly/yearly
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """
        raise NotImplementedError

    def upgrade_recurring_subscription(self, amount: float, plan_type: str,
                                       coupon=None, duration: str = DURATION_MONTHLY, **kwargs):
        """
        Upgrade user's plan to new plan
        :param amount: (float) Money need pay
        :param plan_type: (str) Plan alias
        :param coupon: (obj) PromoCode object
        :param duration: (str) duration: monthly/half_yearly/yearly
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """
        raise NotImplementedError

    def cancel_recurring_subscription(self, **kwargs):
        """
        Cancel current recurring subscription
        :return:
        """
        raise NotImplementedError

    def cancel_immediately_recurring_subscription(self, **kwargs):
        """
        Cancel immediately the subscription
        :return:
        """
        raise NotImplementedError

    def recurring_subtract(self, amount: float, plan_type: str, coupon=None, duration: str = DURATION_MONTHLY,
                           **kwargs):
        """
        Recurring subtract money
        :param amount: (float) Money
        :param plan_type: (str) Plan alias
        :param coupon: (obj) PromoCode object
        :param duration: (str) duration: monthly/half_yearly/yearly
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """
        raise NotImplementedError

    def onetime_payment(self, amount: float, plan_type: str, coupon=None, **kwargs):
        """
        One-time payment
        :param amount: (float) Money
        :param plan_type: (str) Plan alias
        :param coupon: (obj) Promo code object
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """
        raise NotImplementedError

    def update_quantity_subscription(self, new_quantity: int = None, amount: int = None):
        """
        Update the quantity of the subscribed plan
        :param new_quantity:
        :param amount:
        :return:
        """

    def update_default_payment(self, new_source):
        raise NotImplementedError

    def calc_update_total_amount(self, new_plan, new_duration: str, new_quantity: int, **kwargs):
        """
        Calc total amount when user update plan
        :param new_plan:
        :param new_duration:
        :param new_quantity:
        :param kwargs:
        :return:
        """
        raise NotImplementedError
