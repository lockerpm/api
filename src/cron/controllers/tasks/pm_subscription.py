from django.conf import settings
from django.db.models import Count, F

from core.settings import CORE_CONFIG
from shared.constants.transactions import *
from shared.utils.app import now
from shared.background import LockerBackgroundFactory, BG_NOTIFY
# from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
from cystack_models.models.user_plans.pm_user_plan import PMUserPlan


def pm_subscription():
    user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
    # Filter PWD Subscription by VND wallet
    pm_user_plans = PMUserPlan.objects.filter(pm_stripe_subscription__isnull=True).exclude(
        pm_plan__alias=PLAN_TYPE_PM_FREE
    ).exclude(end_period__isnull=True).filter(end_period__lte=now()).annotate(
        family_members_count=Count('user__pm_plan_family')
    ).filter(family_members_count__lt=1)
    for pm_user_plan in pm_user_plans:
        user = pm_user_plan.user
        pm_plan = pm_user_plan.get_plan_obj()
        current_plan_name = pm_plan.get_name()

        # If user cancels at the end of period => Downgrade
        if pm_user_plan.cancel_at_period_end is True:
            user_repository.update_plan(user=user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=settings.SCOPE_PWD_MANAGER)
            LockerBackgroundFactory.get_background(
                bg_name=BG_NOTIFY, background=False
            ).run(func_name="downgrade_plan", **{
                "user_id": user.user_id, "old_plan": current_plan_name, "downgrade_time": now(),
                "scope": settings.SCOPE_PWD_MANAGER
            })
            continue

        # If the subscription by mobile app => Continue
        if pm_user_plan.default_payment_method in [PAYMENT_METHOD_MOBILE]:
            continue

        # Else, check the attempts number
        # TODO: Attempts only apply for the Enterprise plan
        if pm_user_plan.pm_plan.is_team_plan and pm_user_plan.attempts <= MAX_ATTEMPTS:
            pm_user_plan.end_period = PMUserPlan.get_next_attempts_duration(
                current_number_attempts=pm_user_plan.attempts
            ) + now()
            pm_user_plan.attempts = F('attempts') + 1
            pm_user_plan.save()
            # Notify for user here
            LockerBackgroundFactory.get_background(
                bg_name=BG_NOTIFY, background=False
            ).run(func_name="pay_failed", **{
                "user_id": user.user_id,
                "current_attempt": pm_user_plan.attempts,
                "next_attempt": PMUserPlan.get_next_attempts_day_str(current_number_attempts=pm_user_plan.attempts),
                "scope": settings.SCOPE_PWD_MANAGER
            })
        else:
            # Cancel the subscription of the user and notify for this user
            user_repository.update_plan(user=user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=settings.SCOPE_PWD_MANAGER)
            LockerBackgroundFactory.get_background(
                bg_name=BG_NOTIFY, background=False
            ).run(func_name="downgrade_plan", **{
                "user_id": user.user_id, "old_plan": current_plan_name, "downgrade_time": now(),
                "scope": settings.SCOPE_PWD_MANAGER
            })

        # # Else, subtract wallet
        # coupon = pm_user_plan.promo_code
        # if coupon is not None and user.payments.filter(promo_code=coupon).count() >= coupon.duration:
        #     coupon = None
        # amount = pm_user_plan.calc_current_payment_price(currency=CURRENCY_VND)
        # payment_method = PaymentMethodFactory.get_method(
        #     user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_WALLET
        # )
        # subtract_result = payment_method.recurring_subtract(
        #     amount=amount, plan_type=current_plan_name, coupon=coupon, duration=pm_user_plan.duration,
        #     **{"currency": CURRENCY_VND}
        # )
        # # If subtract is failed => Downgrade this current plan
        # if subtract_result.get("success") is False:
        #     user_repository.update_plan(user=user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=settings.SCOPE_PWD_MANAGER)
        #     # Notify for this user
        #     LockerBackgroundFactory.get_background(
        #         bg_name=BG_NOTIFY, background=False
        #     ).run(func_name="downgrade_plan", **{
        #         "user_id": user.user_id, "old_plan": current_plan_name, "downgrade_time": now(),
        #         "scope": settings.SCOPE_PWD_MANAGER
        #     })


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
            link = "https://enterprise.locker.io/admin/billing/payment-method"
        else:
            link = "https://locker.io/settings/plans-billing"
        LockerBackgroundFactory.get_background(
            bg_name=BG_NOTIFY, background=False
        ).run(func_name="banking_expiring", **{
            "user_id": user.user_id,
            "current_plan": plan_name,
            "start_period": pm_user_plan.start_period,
            "end_period": pm_user_plan.end_period,
            "payment_method": pm_user_plan.get_default_payment_method(),
            "scope": settings.SCOPE_PWD_MANAGER,
            "link": link
        })
