from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from core.settings import CORE_CONFIG
from shared.constants.transactions import *


class IPaymentMethod:
    def __init__(self, user, scope):
        self.user = user
        self.scope = scope

    def get_current_plan(self, **kwargs):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        current_plan = user_repository.get_current_plan(user=self.user, scope=self.scope)
        return current_plan

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
        return True

    def recurring_subtract(self, amount: float, plan_type: str,
                           coupon=None, duration: str = DURATION_MONTHLY, **kwargs):
        """
        Recurring subtract money
        :param amount: (float) Money
        :param plan_type: (str) Plan alias
        :param coupon: (obj) PromoCode object
        :param duration: (str) duration: monthly/half_yearly/yearly
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """

    def onetime_payment(self, amount: float, plan_type: str, coupon=None, **kwargs):
        """
        One-time payment
        :param amount: (float) Money
        :param plan_type: (str) Plan alias
        :param coupon: (obj) Promo code object
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """
