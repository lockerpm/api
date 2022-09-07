import os
import traceback
import stripe
import stripe.error

from shared.constants.transactions import *
from shared.log.cylog import CyLog
from shared.utils.app import now
from cystack_models.factory.payment_method.i_payment_method import IPaymentMethod


class StripePaymentMethod(IPaymentMethod):
    @staticmethod
    def handle_error(e):
        """
        Handle stripe subscription
        :param e:
        :return:
        """
        body = e.json_body
        err = body.get("error", {})
        return {
            "stripe_error_type": err.get("type", None),
            "stripe_error_code": err.get("code", None),
            "stripe_error_param": err.get("param") if err.get("param") else None,
            "stripe_error_message": err.get("message", None)
        }

    def create_recurring_subscription(self, amount: float, plan_type: str, coupon=None,
                                      duration: str = DURATION_MONTHLY, **kwargs) -> dict:
        """
        Create new recurring subscription for user
        :param amount: (float) Money need pay
        :param plan_type: (str) Plan alias
        :param coupon: (obj) PromoCode object
        :param duration: (str) duration: monthly/half_yearly/yearly
        :param kwargs: (dict) Metadata: card, bank_id
        :return: (dict) {"success": true/false, "stripe_error": ""}
        """
        # If user does not have card => False
        card = kwargs.get("card")
        if not card or isinstance(card, dict) is False or not card.get("stripe_customer_id"):
            return {"success": False}
        # If duration is not valid
        if duration not in [DURATION_MONTHLY, DURATION_HALF_YEARLY, DURATION_YEARLY]:
            return {"success": False}
        # Re-formatting Stripe coupon
        coupon = None if coupon is None else "{}_{}".format(coupon.id, duration)
        # Re-formatting Stripe plans
        plans = self.__reformatting_stripe_plans(plan_type=plan_type, duration=duration, **kwargs)
        # Create immediate subscription
        try:
            stripe_sub = stripe.Subscription.create(
                customer=card.get("stripe_customer_id"),
                default_payment_method=card.get("id_card"),
                items=plans,
                metadata={
                    "user_id": self.user.user_id,
                    "scope": self.scope,
                    "family_members": str(kwargs.get("family_members", [])),
                    "enterprise_id": kwargs.get("enterprise_id"),
                    "number_members": kwargs.get("number_members", 1)
                },
                coupon=coupon,
                trial_end=kwargs.get("trial_end")
            )
            if kwargs.get("billing_cycle_anchor"):
                stripe.Subscription.modify(
                    stripe_sub.id,
                    trial_end=kwargs.get("billing_cycle_anchor"),
                    proration_behavior='none'
                )
        except stripe.error.CardError as e:
            return {
                "success": False,
                "stripe_error": True,
                "error_details": self.handle_error(e)
            }

        return {"success": True, "stripe_error": False, "error_details": None}

    def upgrade_recurring_subscription(self, amount: float, plan_type: str, coupon=None,
                                       duration: str = DURATION_MONTHLY, **kwargs) -> dict:
        """
        Upgrade user's plan to new plan
        :param amount: (float) Money need pay
        :param plan_type: (str) Plan alias
        :param coupon: (obj) PromoCode object
        :param duration: (str) duration: monthly/half_yearly/yearly
        :param kwargs: (dict) Metadata: card, bank_id
        :return: (dict) {"success": true/false, "stripe_error": ""}
        """
        # If user doesn't have any card => return
        card = kwargs.get("card")
        if not card or isinstance(card, dict) is False or not card.get("stripe_customer_id") or not card.get("id_card"):
            return {"success": False}

        # First, get current user plan
        current_plan = self.get_current_plan(**kwargs)

        stripe_subscription = current_plan.get_stripe_subscription()
        # Create stripe subscription if does not exist
        if not stripe_subscription:
            return self.create_recurring_subscription(amount, plan_type, coupon, duration, **kwargs)
        # Upgrade existed plan
        CyLog.info(**{"message": "Upgrade existed plan: User: {} - kwargs {} - {} {} {}".format(
            self.user, kwargs, plan_type, coupon, duration
        )})
        # Firstly, check old subscription has coupon? If the coupon exists, we will remove old coupon
        if stripe_subscription.discount is not None:
            stripe.Subscription.delete_discount(stripe_subscription.id)

        # Cancel the current plan immediately
        is_cancel_successfully = self.cancel_immediately_recurring_subscription()
        # Then, create new subscription
        if is_cancel_successfully is True:
            return self.create_recurring_subscription(amount, plan_type, coupon, duration, **kwargs)
        else:
            CyLog.error(**{
                "message": "Upgrade existed plan Error: Cannot cancel the current subscription: {} - kwarg {}".format(
                    self.user, kwargs
                )
            })
            return {"success": False, "stripe_error": False, "error_details": None}

        # # Re-formatting Stripe coupon and Stripe plans
        # coupon = None if coupon is None else "{}_{}".format(coupon.id, duration)
        # stripe_plan_id = self.__reformatting_stripe_plan_id(plan_type, duration)
        # try:
        #     """
        #     Here, we update the Stripe subscription.
        #     - Use payment_behavior='pending_if_incomplete' to update subscription using `pending_updates`.
        #     The subscription object will return `pending_update` dict in event webhook
        #     - Use proration_behavior='always_invoice' to invoice immediately for proration.
        #     """
        #     # First, update payment method and metadata
        #     new_stripe_subscription = stripe.Subscription.modify(
        #         stripe_subscription.id,
        #         default_payment_method=card.get("id_card"),
        #         metadata={
        #             "user_id": self.user.user_id,
        #             "scope": self.scope,
        #             "family_members": str(kwargs.get("family_members", [])),
        #             "key": kwargs.get("key"),
        #             "collection_name": kwargs.get("collection_name")
        #         },
        #         coupon=coupon
        #     )
        #     # Update item plan
        #     new_stripe_subscription = stripe.Subscription.modify(
        #         stripe_subscription.id,
        #         payment_behavior='pending_if_incomplete',
        #         proration_behavior='always_invoice',
        #         items=[{
        #             'id': stripe_subscription['items']['data'][0].id,
        #             'plan': stripe_plan_id,
        #             'quantity': self.__get_new_quantity(**kwargs)
        #         }]
        #     )
        # except stripe.error.CardError as e:
        #     CyLog.debug(**{"message": "Upgrade CardError {}".format(self.handle_error(e))})
        #     return {
        #         "success": False,
        #         "stripe_error": True,
        #         "error_details": self.handle_error(e)
        #     }
        # except Exception as e:
        #     tb = traceback.format_exc()
        #     CyLog.debug(**{"message": "Upgrade failed {}".format(tb)})
        #     return {"success": False, "stripe_error": False, "error_details": None}
        #
        # # Upgrade successfully => Upgrade user plan
        # CyLog.info(**{"message": "[Stripe] Start upgrade new plan: {} {} ".format(plan_type, duration)})
        # return {"success": True, "stripe_error": False, "error_details": None}

    def cancel_recurring_subscription(self, **kwargs):
        """
        Cancel current recurring subscription
        We set cancel_at_period_end of stripe subscription is True or False
        :return:
        """
        current_plan = self.get_current_plan(**kwargs)
        stripe_subscription = current_plan.get_stripe_subscription()
        if not stripe_subscription:
            return
        cancel_at_period_end = stripe_subscription.cancel_at_period_end
        stripe.Subscription.modify(
            stripe_subscription.id,
            cancel_at_period_end=True if cancel_at_period_end is False else False
        )
        # Return end time if cancel current stripe subscription
        if cancel_at_period_end is False:
            return stripe_subscription.current_period_end

    def cancel_immediately_recurring_subscription(self, **kwargs):
        current_plan = self.get_current_plan(**kwargs)
        stripe_subscription = current_plan.get_stripe_subscription()
        if not stripe_subscription:
            return True
        try:
            stripe.Subscription.delete(stripe_subscription.id)
            return True
        except stripe.error.StripeError:
            tb = traceback.format_exc()
            CyLog.error(**{"message": "cancel_immediately_recurring_subscription error: {}".format(tb)})
            return False

    def recurring_subtract(self, amount: float, plan_type: str,
                           coupon=None, duration: str = DURATION_MONTHLY, **kwargs):
        pass

    def onetime_payment(self, amount: float, plan_type: str, coupon=None, **kwargs):
        """
        One-time payment
        :param amount: (float) Amount need pay
        :param plan_type: (str) Plan type
        :param coupon: (obj) Promo code object
        :param kwargs: (dict) Metadata: card, bank_id
        :return:
        """

    def update_quantity_subscription(self, new_quantity: int = None, amount: int = None):
        current_plan = self.get_current_plan()
        stripe_subscription = current_plan.get_stripe_subscription()
        if not stripe_subscription or (new_quantity is None and amount is None):
            return
        plan_alias = current_plan.get_plan_obj().get_alias()
        duration = current_plan.duration
        if new_quantity:
            plans = self.__reformatting_stripe_plans(
                plan_type=plan_alias, duration=duration, **{"number_members": new_quantity}
            )
        else:
            old_quantity = stripe_subscription.get("quantity")
            if not old_quantity:
                items = stripe_subscription.items.data
                stripe_plan_id = self.__reformatting_stripe_plan_id(plan_type=plan_alias, duration=duration)
                for item in items:
                    if item.get("plan").get("id") == stripe_plan_id:
                        old_quantity = item.get("quantity")
                        break
            if not old_quantity:
                return
            plans = self.__reformatting_stripe_plans(
                plan_type=plan_alias, duration=duration, **{"number_members": old_quantity + amount}
            )
        try:
            stripe.Subscription.modify(
                stripe_subscription.id,
                items=plans,
                proration_behavior='none'
            )
        except stripe.error.StripeError:
            tb = traceback.format_exc()
            CyLog.error(**{"message": "[update_quantity_subscription] Stripe error: {} {}\n{}".format(
                current_plan, new_quantity, tb
            )})

    def update_default_payment(self, new_source):
        current_plan = self.get_current_plan()
        stripe_subscription = current_plan.get_stripe_subscription()
        if not stripe_subscription or not new_source:
            return
        try:
            stripe.Subscription.modify(stripe_subscription.id, default_payment_method=new_source)
            return new_source
        except stripe.error.StripeError:
            tb = traceback.format_exc()
            CyLog.error(**{"message": "[update_default_payment] Stripe error: {} {}\n{}".format(
                current_plan, new_source, tb
            )})

    def calc_update_total_amount(self, new_plan, new_duration, new_quantity, **kwargs):
        """
        Calc total amount when user update plan (via upgrade current plan or ...)
        :param new_plan: (obj) New Plan object
        :param new_duration: (str) New duration: monthly/yearly/...
        :param new_quantity: (int) New quantity
        :return:
        """
        current_plan = kwargs.get("current_plan")
        if not current_plan:
            current_plan = self.get_current_plan(**kwargs)
        current_stripe_sub = current_plan.get_stripe_subscription()
        # Retrieve discount applied of this current Stripe Subscription
        discount_applied = current_stripe_sub.discount
        amount_off = None
        percent_off = None
        if discount_applied is not None:
            amount_off = discount_applied.coupon.amount_off
            percent_off = discount_applied.coupon.percent_off

        current_period_start = current_stripe_sub.get("current_period_start")
        current_period_end = current_stripe_sub.get("current_period_end")
        current_time = now()
        old_price = current_stripe_sub.get("plan").get("amount") / 100
        old_amount = old_price * current_stripe_sub.get("quantity", 1)
        if amount_off is not None:
            old_amount = max(old_amount - amount_off / 100, 0)
        if percent_off is not None:
            old_amount = max(old_amount * (1 - percent_off / 100), 0)
        old_duration = current_plan.duration

        new_plan_price = new_plan.get_price(duration=new_duration, currency=CURRENCY_USD)
        # Money used: (now - start) / (end - start) * old_price
        # Money remain: old_price - money_used
        # => Diff price: new_price - money_remain
        if old_duration == new_duration:
            old_remain = old_amount * (
                1 - (current_time - current_period_start) / (current_period_end - current_period_start)
            )
            new_remain = new_plan_price * new_quantity * (
                (current_period_end - current_time) / (current_period_end - current_period_start)
            )
            total_amount = new_remain - old_remain
            next_billing_time = current_plan.get_next_billing_time(duration=new_duration)
            print("DIFF AMOUNT SAME DURATION ", total_amount)
        else:
            old_used = old_amount * (
                (current_time - current_period_start) / (current_period_end - current_period_start)
            )
            old_remain = old_amount - old_used
            total_amount = new_plan_price * new_quantity - old_remain
            next_billing_time = current_time + self.__get_duration_next_billing_month(new_duration) * 30 * 86400
            print("DIFF AMOUNT DIFF DURATION ", total_amount)
        return round(total_amount, 2), next_billing_time

    def __reformatting_stripe_plans(self, plan_type: str, duration: str, **kwargs):
        stripe_plan_id = self.__reformatting_stripe_plan_id(plan_type, duration)
        return [{"plan": stripe_plan_id, "quantity": self.__get_new_quantity(**kwargs)}]

    @staticmethod
    def __reformatting_stripe_plan_id(plan_type: str, duration: str):
        stripe_plan_id = "{}_{}".format(plan_type, duration).lower()
        # Re-mapping stripe plan
        real_stripe_plans = {}
        if os.getenv("PROD_ENV") == "staging":
            real_stripe_plans["pm_enterprise_monthly"] = "locker_pm_enterprise_monthly"

        return real_stripe_plans.get(stripe_plan_id, stripe_plan_id)

    @staticmethod
    def __get_new_quantity(**kwargs):
        # If scope is password manager
        return kwargs.get("number_members", 1)

    @staticmethod
    def __get_duration_next_billing_month(duration):
        if duration == DURATION_YEARLY:
            return 12
        elif duration == DURATION_HALF_YEARLY:
            return 6
        return 1

    # def __get_current_quantity(self, user_plan):
    #     return user_plan.number_members
