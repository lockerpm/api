import os
import traceback

import stripe
import stripe.error

from locker_server.shared.constants.transactions import *
from locker_server.shared.external_services.payment_method.payment_method import PaymentMethod
from locker_server.shared.log.cylog import CyLog


class StripePaymentMethod(PaymentMethod):
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

    @staticmethod
    def __reformatting_stripe_plan_id(plan_type: str, duration: str):
        stripe_plan_id = "{}_{}".format(plan_type, duration).lower()
        # Re-mapping stripe plan
        real_stripe_plans = {}
        if os.getenv("PROD_ENV") == "staging":
            real_stripe_plans["pm_enterprise_monthly"] = "locker_pm_enterprise_monthly"
        elif os.getenv("PROD_ENV") == "prod":
            real_stripe_plans["pm_family_yearly"] = "locker_pm_family_yearly"

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

    def __reformatting_stripe_plans(self, plan_type: str, duration: str, **kwargs):
        stripe_plan_id = self.__reformatting_stripe_plan_id(plan_type, duration)
        return [{"plan": stripe_plan_id, "quantity": self.__get_new_quantity(**kwargs)}]

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
        coupon = None if coupon is None else "{}_{}".format(coupon.promo_code_id, duration)
        # Re-formatting Stripe plans
        plans = self.__reformatting_stripe_plans(plan_type=plan_type, duration=duration, **kwargs)
        # Create immediate subscription
        trial_end = kwargs.get("trial_end")
        billing_cycle_anchor = kwargs.get("billing_cycle_anchor")
        billing_cycle_anchor_action = kwargs.get("billing_cycle_anchor_action") or "update"

        try:
            stripe_sub_metadata = {
                "user_id": self.user_plan.user.user_id,
                "scope": self.scope,
                "family_members": str(kwargs.get("family_members", [])),
                "enterprise_id": kwargs.get("enterprise_id"),
                "number_members": kwargs.get("number_members", 1)
            }
            if billing_cycle_anchor and billing_cycle_anchor_action == "set":
                # Set billing_cycle_anchor to void 0 USD invoice from Stripe
                # https://stripe.com/docs/billing/subscriptions/billing-cycle
                stripe_sub = stripe.Subscription.create(
                    customer=card.get("stripe_customer_id"),
                    default_payment_method=card.get("id_card"),
                    items=plans,
                    metadata=stripe_sub_metadata,
                    coupon=coupon,
                    billing_cycle_anchor=billing_cycle_anchor,
                    proration_behavior='none'
                )
            else:
                stripe_sub = stripe.Subscription.create(
                    customer=card.get("stripe_customer_id"),
                    default_payment_method=card.get("id_card"),
                    items=plans,
                    metadata=stripe_sub_metadata,
                    coupon=coupon,
                    trial_end=trial_end
                )
                if billing_cycle_anchor:
                    stripe.Subscription.modify(
                        stripe_sub.id,
                        trial_end=billing_cycle_anchor,
                        proration_behavior='none'
                    )
        except stripe.error.CardError as e:
            return {
                "success": False,
                "stripe_error": True,
                "error_details": self.handle_error(e)
            }

        return {"success": True, "stripe_error": False, "error_details": None, "stripe_subscription_id": stripe_sub.id}

    def upgrade_recurring_subscription(self, amount: float, plan_type: str,
                                       coupon=None, duration: str = DURATION_MONTHLY, **kwargs):
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
        current_plan = self.get_current_plan()
        stripe_subscription = current_plan.get_stripe_subscription()
        # Create stripe subscription if it does not exist
        if not stripe_subscription:
            return self.create_recurring_subscription(amount, plan_type, coupon, duration, **kwargs)
        # Upgrade existed plan
        CyLog.info(**{"message": "Upgrade existed plan: User: {} - kwargs {} - {} {} {}".format(
            self.user_plan.user.user_id, kwargs, plan_type, coupon, duration
        )})
        # Firstly, check old subscription has coupon? If the coupon exists, we will remove old coupon
        if stripe_subscription.discount is not None:
            stripe.Subscription.delete_discount(stripe_subscription.id)

        # Re-formatting Stripe coupon and Stripe plans
        coupon = None if coupon is None else "{}_{}".format(coupon.promo_code_id, duration)
        stripe_plan_id = self.__reformatting_stripe_plan_id(plan_type, duration)
        try:
            """
            Here, we update the Stripe subscription.
            - Use payment_behavior='pending_if_incomplete' to update subscription using `pending_updates`.
            The subscription object will return `pending_update` dict in event webhook
            - Use proration_behavior='always_invoice' to invoice immediately for proration.
            """
            # First, update payment method and metadata
            stripe.Subscription.modify(
                stripe_subscription.id,
                default_payment_method=card.get("id_card"),
                metadata={
                    "user_id": self.user_plan.user.user_id,
                    "scope": self.scope,
                    "family_members": str(kwargs.get("family_members", [])),
                    "key": kwargs.get("key"),
                    "collection_name": kwargs.get("collection_name")
                },
                coupon=coupon
            )
            # Update item plan
            new_stripe_subscription = stripe.Subscription.modify(
                stripe_subscription.id,
                payment_behavior='pending_if_incomplete',
                proration_behavior='none',
                items=[{
                    'id': stripe_subscription['items']['data'][0].id,
                    'plan': stripe_plan_id,
                    'quantity': self.__get_new_quantity(**kwargs)
                }]
            )
        except stripe.error.CardError as e:
            CyLog.debug(**{"message": "Upgrade CardError {}".format(self.handle_error(e))})
            return {
                "success": False,
                "stripe_error": True,
                "error_details": self.handle_error(e)
            }
        except Exception as e:
            tb = traceback.format_exc()
            CyLog.debug(**{"message": "Upgrade failed {}".format(tb)})
            return {"success": False, "stripe_error": False, "error_details": None}

        # Upgrade successfully => Upgrade user plan
        CyLog.info(**{"message": "[Stripe] Start upgrade new plan: {} {} ".format(plan_type, duration)})
        return {
            "success": True,
            "stripe_error": False,
            "error_details": None,
            "stripe_subscription_id": new_stripe_subscription.id
        }

    def cancel_recurring_subscription(self, **kwargs):
        """
        Cancel current recurring subscription
        We set cancel_at_period_end of stripe subscription is True or False
        :return:
        """
        current_plan = self.get_current_plan()
        stripe_subscription = current_plan.get_stripe_subscription()
        if not stripe_subscription:
            return
        if "cancel_at_period_end" not in kwargs:
            stripe_cancel_at_period_end = stripe_subscription.cancel_at_period_end
            cancel_at_period_end = True if stripe_cancel_at_period_end is False else False
        else:
            cancel_at_period_end = kwargs.get("cancel_at_period_end")
        stripe.Subscription.modify(
            stripe_subscription.id,
            cancel_at_period_end=cancel_at_period_end
        )
        # Return end time if cancel current stripe subscription
        if cancel_at_period_end is False:
            return stripe_subscription.current_period_end

    def cancel_immediately_recurring_subscription(self, **kwargs):
        current_plan = self.get_current_plan()
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

    def recurring_subtract(self, amount: float, plan_type: str, coupon=None, duration: str = DURATION_MONTHLY,
                           **kwargs):
        pass

    def onetime_payment(self, amount: float, plan_type: str, coupon=None, **kwargs):
        from locker_server.containers.containers import payment_service, user_service

        card = kwargs.get("card")
        if not card or isinstance(card, dict) is False or not card.get("stripe_customer_id"):
            return {"success": False}
        stripe_customer_id = card.get("stripe_customer_id")

        # Crete new billing history
        try:
            promo_code_str = coupon.promo_code_id if coupon else None
        except AttributeError:
            promo_code_str = None

        new_payment_data = {
            "user_id": self.user_plan.user.user_id,
            "description": "Upgrade plan onetime payment",
            "plan": plan_type,
            "payment_method": PAYMENT_METHOD_CARD,
            "duration": "lifetime",
            "currency": CURRENCY_USD,
            "promo_code": promo_code_str,
            "customer": user_service.get_customer_data(user=self.user_plan.user, id_card=card.get("id_card")),
            "scope": self.scope,
            "metadata": kwargs
        }
        new_payment = payment_service.create_payment(**new_payment_data)
        # Create new invoice item
        stripe.InvoiceItem.create(
            customer=stripe_customer_id,
            description="Upgrade plan onetime payment",
            unit_amount=int(amount * 100),
            currency="USD",
            metadata={
                "scope": self.scope,
                "user_id": self.user_plan.user.user_id,
                "plan": plan_type
            }
        )
        # Then, create onetime invoice for the user
        new_stripe_invoice = stripe.Invoice.create(
            customer=stripe_customer_id,
            default_payment_method=card.get("id_card"),
            metadata={
                "scope": self.scope,
                "user_id": self.user_plan.user.user_id,
                "payment_id": new_payment.payment_id,
            }
        )
        # Finalize new stripe invoice
        stripe_invoice_id = new_stripe_invoice.get("id")
        stripe.Invoice.finalize_invoice(stripe_invoice_id)
        try:
            paid_invoice = stripe.Invoice.pay(stripe_invoice_id)
            print(paid_invoice)
        except stripe.error.CardError as e:
            return {
                "success": False,
                "stripe_error": True,
                "error_details": self.handle_error(e)
            }

        new_payment = payment_service.update_payment(payment=new_payment, update_data={
            "stripe_invoice_id": stripe_invoice_id,
            "status": PAYMENT_STATUS_PAID
        })
        return {
            "success": True,
            "payment_id": new_payment.payment_id
        }

    def update_quantity_subscription(self, new_quantity: int = None, amount: int = None):
        """
        Update the quantity of the subscribed plan
        :param new_quantity:
        :param amount:
        :return:
        """
        current_plan = self.get_current_plan()
        stripe_subscription = current_plan.get_stripe_subscription()
        if not stripe_subscription or (new_quantity is None and amount is None):
            return
        plan_alias = current_plan.pm_plan.alias
        duration = current_plan.duration

        si = None
        old_quantity = stripe_subscription.get("quantity")
        items = stripe_subscription.get("items").get("data")
        stripe_plan_id = self.__reformatting_stripe_plan_id(plan_type=plan_alias, duration=duration)
        for item in items:
            if item.get("plan").get("id") == stripe_plan_id:
                old_quantity = item.get("quantity")
                si = item.get("id")
                break
        if not si:
            return
        if new_quantity:
            plans = [{"id": si, "quantity": new_quantity}]
        else:
            if not old_quantity:
                return
            plans = [{"id": si, "quantity": old_quantity + amount}]
        try:
            stripe.Subscription.modify(
                stripe_subscription.id,
                items=plans,
                proration_behavior='none'
            )
        except stripe.error.StripeError:
            tb = traceback.format_exc()
            CyLog.error(**{"message": "[update_quantity_subscription] Stripe error: {} {}\n{}".format(
                current_plan, plans, tb
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

    # def calc_update_total_amount(self, new_plan, new_duration: str, new_quantity: int, **kwargs):
    #     """
    #     Calc total amount when user update plan
    #     :param new_plan:
    #     :param new_duration:
    #     :param new_quantity:
    #     :param kwargs:
    #     :return:
    #     """
    #     # raise NotImplementedError
    #     pass
