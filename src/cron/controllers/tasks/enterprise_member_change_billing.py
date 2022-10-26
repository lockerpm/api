import stripe
import stripe.error

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory, \
    PaymentMethodNotSupportException
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

        pay_quantity = quantity
        # Check init seats
        if enterprise.init_seats and enterprise.init_seats_expired_time and \
                current_time < enterprise.init_seats_expired_time:
            num_active_members = enterprise.get_activated_members_count()
            pay_quantity = max(num_active_members - enterprise.init_seats, 0)
        if pay_quantity <= 0:
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
            description=f"{pay_quantity} member(s) added into Locker Enterprise",
            unit_amount=int(unit_amount * 100),
            currency="USD",
            quantity=pay_quantity,
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
                # Auto collect all-pending invoice item
                collection_method="charge_automatically",
                pending_invoice_items_behavior="include",
                metadata={
                    "scope": settings.SCOPE_PWD_MANAGER,
                    "user_id": primary_admin_user.user_id,
                    "category": "member_changes",
                    "added_user_ids": added_user_ids_str,
                    # The invoice is one-time invoice and the `subscription` property of the invoice object is null
                    # So that we need to set `stripe_subscription_id` in the metadata
                    "stripe_subscription_id": user_plan.pm_stripe_subscription
                }
            )
            try:
                paid_invoice = stripe.Invoice.pay(new_change_member_invoice.get("id"))
                print(paid_invoice)
            except stripe.error.CardError:
                print("Card Error. So disable added members")
                # Payment failed => Disable members
                disabled_members = enterprise.enterprise_members.filter(
                    user_id__in=added_user_ids
                ).update(is_activated=False)
                print("DISABLED MEMBERS, ", disabled_members)
                try:
                    PaymentMethodFactory.get_method(
                        user=enterprise.get_primary_admin_user(), scope=settings.SCOPE_PWD_MANAGER,
                        payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=-disabled_members)
                except (PaymentMethodNotSupportException, ObjectDoesNotExist):
                    pass
        else:
            pass

        user_plan.member_billing_updated_time = current_time
        user_plan.save()
