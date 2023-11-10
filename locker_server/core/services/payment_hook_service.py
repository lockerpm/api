from typing import List, Dict

import stripe

from locker_server.core.entities.payment.payment import Payment
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.payment_exception import PaymentInvoiceDoesNotExistException
from locker_server.core.repositories.payment_repository import PaymentRepository
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.transactions import *
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.utils.app import now


class PaymentHookService:
    """
    This class represents Use Cases related Payment webhook
    """
    def __init__(self, payment_repository: PaymentRepository,
                 user_plan_repository: UserPlanRepository,
                 user_repository: UserRepository):
        self.payment_repository = payment_repository
        self.user_plan_repository = user_plan_repository
        self.user_repository = user_repository

    def webhook_create(self, **hook_data):
        description = hook_data.get("description", "")
        user_id = hook_data.get("user_id")
        scope = hook_data.get("scope")
        promo_code = hook_data.get("promo_code")
        paid = hook_data.get("paid", True)
        duration = hook_data.get("duration", DURATION_MONTHLY)
        total = hook_data.get("total")
        subtotal = hook_data.get("subtotal")
        stripe_invoice_id = hook_data.get("stripe_invoice_id")
        stripe_subscription_id = hook_data.get("stripe_subscription_id")
        failure_reason = hook_data.get("failure_reason")
        currency = hook_data.get("currency", CURRENCY_USD)
        plan = hook_data.get("plan")

        # Check this invoice with stripe_invoice_id existed                                           ?
        stripe_invoice_exist = None
        stripe_subscription_obj = None
        stripe_card_id = None
        if stripe_invoice_id:
            stripe_invoice_exist = self.payment_repository.get_by_stripe_invoice_id(stripe_invoice_id=stripe_invoice_id)
        if stripe_subscription_id:
            stripe_subscription_obj = stripe.Subscription.retrieve(stripe_subscription_id)
            stripe_card_id = stripe_subscription_obj.default_payment_method

        # If we don't have a payment with stripe_invoice_id => Create new one
        if not stripe_invoice_exist:
            user, is_created = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
            new_payment_data = {
                "user_id": user.user_id,
                "description": description,
                "plan": plan,
                "duration": duration,
                "promo_code": promo_code,
                "currency": currency,
                "mobile_invoice_id": None,
                "stripe_invoice_id": stripe_invoice_id,
                "customer": self.user_repository.get_customer_data(user=user, id_card=stripe_card_id),
                "metadata": stripe_subscription_obj.get("metadata", {}) if stripe_subscription_obj else {}
            }
            if promo_code:
                promo_code_id = promo_code.replace("_half_yearly", "").replace("_yearly", "").replace("_monthly", "")
                new_payment_data["promo_code"] = promo_code_id
            # Find payments items
            payments_items = []
            new_payment_data["payments_items"] = payments_items

            new_payment = self.payment_repository.create_payment(**new_payment_data)
            # Set total amount
            if total is not None:
                new_total_price = round(float(total / 100), 2)
                new_payment = self.payment_repository.update_payment(payment=new_payment, update_data={
                    "total_price": abs(new_total_price),
                    "discount": round(float((subtotal - total) / 100), 2),
                    "transaction_type": TRANSACTION_TYPE_REFUND if new_total_price < 0 else new_payment.transaction_type,
                })
                # Else, retrieving the payment with stripe_payment_id
        else:
            new_payment = stripe_invoice_exist

        result = {}
        extra_time = 0
        extra_plan = None
        if paid is True:
            new_payment = self.payment_repository.set_paid(payment=new_payment)
            if stripe_subscription_obj:
                pm_user_plan = self.user_plan_repository.get_user_plan(user_id=new_payment.user.user_id)
                # if this user is in a trial plan => Set extra time
                if pm_user_plan.end_period and pm_user_plan.pm_stripe_subscription is None:
                    extra_time = max(pm_user_plan.end_period - now(), 0)
                    extra_plan = pm_user_plan.pm_plan.alias

                self.user_plan_repository.update_user_plan_by_id(
                    user_plan_id=pm_user_plan.pm_user_plan_id, user_plan_update_data={
                        "pm_stripe_subscription": stripe_subscription_id,
                        "pm_stripe_subscription_created_time": now(),
                        "personal_trial_applied": True if stripe_subscription_obj.status == "trialing"
                        else pm_user_plan.personal_trial_applied,
                        "personal_trial_web_applied": True if stripe_subscription_obj.status == "trialing"
                        else pm_user_plan.personal_trial_web_applied
                    }
                )
                start_period = stripe_subscription_obj.current_period_start
                end_period = stripe_subscription_obj.current_period_end
                # Upgrade the plan of this user
                subscription_metadata = {
                    "start_period": start_period,
                    "end_period": end_period,
                    "promo_code": new_payment.promo_code,
                    "family_members": stripe_subscription_obj.get("metadata", {}).get("family_members", []),
                    "extra_time": extra_time,
                    "extra_plan": extra_plan
                }
                updated_user_plan = self.user_plan_repository.update_plan(
                    user_id=new_payment.user.user_id, plan_type_alias=new_payment.plan, duration=new_payment.duration,
                    scope=scope, **subscription_metadata
                )
                enterprise = self.user_plan_repository.get_default_enterprise(user_id=new_payment.user.user_id)
                result["payment_data"] = {
                    "enterprise_id": enterprise.enterprise_id if enterprise else None,
                    "enterprise_name": enterprise.name if enterprise else None,
                    "stripe_invoice_id": new_payment.stripe_invoice_id,
                    "plan_name": updated_user_plan.pm_plan.name,
                    "plan_price": updated_user_plan.pm_plan.get_price(
                        currency=new_payment.currency, duration=new_payment.duration
                    ),
                    "number_members": int(new_payment.metadata.get("number_members", 1)) or 1,
                    "start_period": start_period,
                    "end_period": end_period,
                }

        else:
            new_payment = self.payment_repository.set_failed(payment=new_payment, failure_reason=failure_reason)
        result["new_payment"] = new_payment

        return result

    def webhook_set_status(self, payment: Payment, payment_status: str, failure_reason: str = None,
                           locker_web_url: str = None) -> Dict:
        user = payment.user
        payment_data = {
            "user_id": user.user_id,
            "success": True,
            "payment_id": payment.payment_id,
            "order_date": payment.get_created_time_str(),
            "total_money": "{}".format(payment.total_price),
            "currency": payment.currency,
            "paid": True if payment_status == PAYMENT_STATUS_PAID else False,
            "payment_method": PAYMENT_METHOD_CARD,
            "created_time": payment.created_time
        }

        current_plan = self.user_plan_repository.get_user_plan(user_id=user.user_id)
        payment_data.update({
            "current_plan": current_plan.pm_plan.name,
            "total_price": payment.total_price,
            "duration": payment.duration,
            "plan_price": current_plan.pm_plan.get_price(duration=payment.duration, currency=payment.currency),
            "url": "{}/invoices/{}".format(locker_web_url, payment.payment_id),
        })
        if payment_status == PAYMENT_STATUS_PAID:
            self.payment_repository.set_paid(payment=payment)
        elif payment_status == PAYMENT_STATUS_PAST_DUE:
            self.payment_repository.set_past_due(payment=payment, failure_reason=failure_reason)
            payment_data.update({"reason": failure_reason})
        elif payment_status == PAYMENT_STATUS_FAILED:
            self.payment_repository.set_failed(payment=payment, failure_reason=failure_reason)
            payment_data.update({"reason": failure_reason})
        return payment_data

    def webhook_unpaid_subscription(self, user: User) -> User:
        current_plan = self.user_plan_repository.get_user_plan(user_id=user.user_id)
        stripe_subscription = current_plan.get_stripe_subscription()
        if stripe_subscription:
            stripe.Subscription.retrieve(stripe_subscription.id).delete()
        return user

    def webhook_cancel_subscription(self, user: User, plan: str, scope: str = None) -> str:
        payment_data = {}
        current_plan = self.user_plan_repository.get_user_plan(user_id=user.user_id)
        old_plan = current_plan.pm_plan.name
        current_plan = self.user_plan_repository.update_user_plan_by_id(
            user_plan_id=current_plan.pm_user_plan_id,
            user_plan_update_data={
                "pm_stripe_subscription": None,
                "pm_stripe_subscription_created_time": None,
                "promo_code": None
            }
        )
        # If this plan is cancelled because the Personal Plan upgrade to Enterprise Plan => Not downgrade
        if self.user_plan_repository.is_update_personal_to_enterprise(current_plan=current_plan, new_plan_alias=plan):
            return old_plan
        # If this plan is cancelled because the Lifetime upgrade => Not downgrade
        if current_plan.pm_plan.alias == PLAN_TYPE_PM_LIFETIME and plan != PLAN_TYPE_PM_LIFETIME:
            return old_plan
        # If this plan is cancelled because the Family Lifetime upgrade => Not downgrade
        if current_plan.pm_plan.alias == PLAN_TYPE_PM_LIFETIME_FAMILY and plan != PLAN_TYPE_PM_LIFETIME_FAMILY:
            return old_plan
        # if this plan is canceled because the user is added into family plan => Not notify
        if not self.user_plan_repository.is_family_member(user_id=user.user_id):
            self.user_plan_repository.update_plan(
                user_id=user.user_id, plan_type_alias=PLAN_TYPE_PM_FREE, scope=scope
            )
            # Notify downgrade here
            BackgroundFactory.get_background(
                bg_name=BG_NOTIFY, background=True
            ).run(func_name="downgrade_plan", **{
                "user_id": user.user_id, "old_plan": old_plan, "downgrade_time": now(),
                "scope": scope, **{"payment_data": payment_data}
            })
        return old_plan

    def banking_callback(self, code: str, amount: float):
        invoice = self.payment_repository.get_by_banking_code(code=code)
        if not invoice:
            raise PaymentInvoiceDoesNotExistException
        if invoice.total_price > amount:
            invoice = self.payment_repository.set_failed(payment=invoice, failure_reason="Not enough money")
        else:
            invoice = self.payment_repository.set_paid(payment=invoice)
            user = invoice.user
            plan_metadata = invoice.metadata
            plan_metadata.update({"promo_code": invoice.promo_code})
            self.user_plan_repository.update_plan(
                user_id=user.user_id, plan_type_alias=invoice.plan, duration=invoice.duration, scope=invoice.scope,
                **plan_metadata
            )
            # Send mail
            BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="pay_successfully", **{"payment": invoice}
            )
        return invoice

    def count_referral_payment(self, referral_user_ids: List[int]) -> int:
        return self.payment_repository.count_referral_payments(referral_user_ids=referral_user_ids)

    def list_enterprise_billing_emails(self, enterprise_id: str) -> List[str]:
        # TODO: Get list billing emails of the enterprise HERE
        return []
