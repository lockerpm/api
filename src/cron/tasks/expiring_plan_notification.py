import time
import schedule
import stripe

from django.conf import settings
from django.db import close_old_connections
from django.db.models import F

from cron.task import Task
from core.settings import CORE_CONFIG
from core.utils.data_helpers import convert_readable_date
from cystack_models.models.user_plans.pm_user_plan import PMUserPlan
from cystack_models.models.payments.payments import Payment
from cystack_models.models.events.events import Event
from shared.background.implements import NotifyBackground
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.event import *
from shared.constants.transactions import *
from shared.utils.app import now


class ExpiringPlanNotification(Task):
    def __init__(self):
        super(ExpiringPlanNotification, self).__init__()
        self.job_id = 'expiring_plan_notification'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()

        try:
            self.pm_expiring_notify()
        except Exception as e:
            self.logger.error()
        # Close old connections
        close_old_connections()
        self.pm_enterprise_reminder()

    @staticmethod
    def pm_expiring_notify():
        # Filter PWD Plan nearly expired - Only notify to Trial users
        current_time = now()
        expiring_plans = PMUserPlan.objects.exclude(
            pm_plan__alias=PLAN_TYPE_PM_FREE
        ).exclude(end_period__isnull=True).annotate(
            plan_period=F('end_period') - F('start_period'),
        ).filter(
            plan_period__lte=15 * 86400, plan_period__gt=0
        ).exclude(cancel_at_period_end=True).filter(
            end_period__gte=current_time + 5 * 86400,
            end_period__lte=current_time + 7 * 86400
        ).select_related('pm_plan')

        for pm_user_plan in expiring_plans:
            user = pm_user_plan.user
            plan_obj = pm_user_plan.get_plan_obj()
            plan_name = plan_obj.get_name()
            if plan_obj.is_team_plan:
                payment_url = "https://enterprise.locker.io/admin/billing/payment-method"
            else:
                payment_url = "https://locker.io/settings/plans-billing"
            LockerBackgroundFactory.get_background(
                bg_name=BG_NOTIFY, background=False
            ).run(func_name="banking_expiring", **{
                "user_id": user.user_id,
                "current_plan": plan_name,
                "start_period": pm_user_plan.start_period,
                "end_period": pm_user_plan.end_period,
                "payment_method": pm_user_plan.get_default_payment_method(),
                "scope": settings.SCOPE_PWD_MANAGER,
                "payment_url": payment_url
            })

    @staticmethod
    def pm_enterprise_reminder():
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        current_time = now()
        expiring_enterprise_plans = PMUserPlan.objects.filter(pm_plan__alias=PLAN_TYPE_PM_ENTERPRISE).filter(
            pm_stripe_subscription__isnull=False, end_period__isnull=False,
        ).filter(
            end_period__gte=current_time + 4 * 86400,
            end_period__lte=current_time + 5 * 86400
        ).select_related('pm_plan')

        for enterprise_plan in expiring_enterprise_plans:
            stripe_subscription = enterprise_plan.get_stripe_subscription()
            if not stripe_subscription:
                continue
            enterprise = user_repository.get_default_enterprise(user=enterprise_plan.user)
            if not enterprise:
                continue
            start_period = enterprise_plan.start_period
            end_period = enterprise_plan.end_period

            added_events = Event.objects.filter(
                team_id=enterprise.id, type__in=[EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_CONFIRMED],
                creation_date__range=(start_period, end_period)
            )
            added_members = len(list(added_events.values_list('user_id', flat=True).distinct()))
            removed_events = Event.objects.filter(
                team_id=enterprise.id, type__in=[EVENT_E_MEMBER_REMOVED, EVENT_E_MEMBER_DISABLED],
                creation_date__range=(start_period, end_period)
            )
            removed_members = len(list(removed_events.values_list('user_id', flat=True).distinct()))

            current_active_members = enterprise.get_activated_members_count()

            upcoming_invoice = stripe.Invoice.upcoming(subscription=stripe_subscription.id)
            lines = upcoming_invoice.lines.data
            old_active_members = None
            for line in lines:
                if line.get("plan"):
                    old_active_members = line.get("quantity")
                    break
            next_payment_date = end_period + Payment.get_duration_month_number(
                duration=enterprise_plan.duration
            ) * 30 * 86400
            next_amount = current_active_members * enterprise_plan.pm_plan.get_price(duration=enterprise_plan.duration)
            payment_method = stripe_subscription.default_payment_method or stripe_subscription.default_source
            last4 = None
            if payment_method:
                last4 = stripe.PaymentMethod.retrieve(payment_method).get("card", {}).get("last4")

            NotifyBackground(background=False).notify_enterprise_next_cycle(data={
                "user_ids": [enterprise_plan.user_id],
                "date_1": convert_readable_date(start_period, datetime_format="%d/%m/%Y"),
                "date_2": convert_readable_date(end_period, datetime_format="%d/%m/%Y"),
                "date_3": convert_readable_date(next_payment_date, datetime_format="%d/%m/%Y"),
                "active_member_count_first_date": old_active_members,
                "added_member_count": added_members,
                "removed_member_count": removed_members,
                "billed_member_count_next_cycle": current_active_members,
                "next_cycle_cost": next_amount,
                "card_ending": last4,
            })

    def scheduling(self):
        schedule.every().day.at("19:30").do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
