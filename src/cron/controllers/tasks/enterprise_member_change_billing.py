import stripe
from datetime import datetime

from django.conf import settings

from cystack_models.models.events.events import Event
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.payments.payments import Payment
from shared.constants.event import EVENT_E_MEMBER_CONFIRMED, EVENT_E_MEMBER_ENABLED
from shared.constants.transactions import *
from shared.utils.app import now


def enterprise_member_change_billing():
    current_time = now()
    enterprises = Enterprise.objects.filter(locked=False)
    for enterprise in enterprises:
        primary_admin_user = enterprise.get_primary_admin_user()
        user_plan = primary_admin_user.pm_user_plan

        # Only accept stripe subscription
        stripe_subscription = user_plan.get_stripe_subscription()
        if not stripe_subscription or not user_plan.start_period or not user_plan.end_period:
            continue

        if user_plan.member_billing_updated_time:
            member_billing_updated_time = user_plan.member_billing_updated_time
        else:
            member_billing_updated_time = current_time - 86400
        pm_plan = user_plan.get_plan_obj()
        pm_plan_price = pm_plan.get_price(duration=user_plan.duration, currency="USD")

        # Calc added event
        added_events = Event.objects.filter(
            team_id=enterprise.id, type__in=[EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_CONFIRMED],
            creation_date__range=(member_billing_updated_time, current_time)
        )
        quantity = added_events.count()
        if quantity == 0:
            continue
        added_user_ids = list(added_events.values_list('user_id', flat=True).distinct())
        added_user_ids_str = ",".join(str(v) for v in added_user_ids)

        # Calc prorations
        diff_days = round((user_plan.end_period - current_time) / 86400, 0)
        unit_amount = pm_plan_price * (
            diff_days / (Payment.get_duration_month_number(duration=user_plan.duration) * 30)
        )

        # Adding invoice items for future invoice
        # https://stripe.com/docs/billing/invoices/subscription#adding-upcoming-invoice-items
        new_added_invoice_item = stripe.InvoiceItem.create(
            customer=stripe_subscription.customer,
            description=f"{quantity} member(s) added into Locker Enterprise",
            unit_amount=int(unit_amount * 100),
            currency="USD",
            quantity=quantity,
            subscription=stripe_subscription.id,
            metadata={
                "scope": settings.SCOPE_PWD_MANAGER,
                "user_id": primary_admin_user.user_id,
                "category": "member_changes",
                "added_user_ids": added_user_ids_str
            }
        )
        print(new_added_invoice_item)

        if user_plan.duration == DURATION_YEARLY:
            # Create new invoice and pay immediately
            new_change_member_invoice = stripe.Invoice.create(
                customer=stripe_subscription.customer,
                collection_method="charge_automatically",
                pending_invoice_items_behavior="include",
                metadata={
                    "scope": settings.SCOPE_PWD_MANAGER,
                    "user_id": primary_admin_user.user_id,
                    "category": "member_changes",
                    "added_user_ids": added_user_ids_str,
                    "stripe_subscription_id": user_plan.pm_stripe_subscription
                }
            )
            paid_invoice = stripe.Invoice.pay(new_change_member_invoice.get("id"))
            print(paid_invoice)
        else:
            pass

        user_plan.member_billing_updated_time = current_time
        user_plan.save()
