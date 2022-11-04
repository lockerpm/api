from django.db.models import F

from cystack_models.models import User, EnterpriseMember
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from shared.utils.app import now


def tutorial_reminder():
    current_time = now()

    users = User.objects.filter()
    enterprise_user_ids = EnterpriseMember.objects.filter(
        status=E_MEMBER_STATUS_CONFIRMED
    ).values_list('user_id', flat=True)
    exclude_enterprise_users = users.exclude(user_id__in=enterprise_user_ids)

    # 3 days
    users_3days = users.filter(
        creation_date__range=(current_time - 4 * 86400, current_time - 3 * 86400)
    ).values_list('user_id', flat=True)
    LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
        func_name="notify_tutorial", **{
            "job": "tutorial_day_3_add_items", "user_ids": list(users_3days),
        }
    )

    # 5 days
    users_5days = users.filter(
        creation_date__range=(current_time - 6 * 86400, current_time - 5 * 86400)
    ).values_list('user_id', flat=True)
    LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
        func_name="notify_tutorial", **{
            "job": "tutorial_day_5_download", "user_ids": list(users_5days),
        }
    )

    # 7 days
    users_7days = users.filter(
        creation_date__range=(current_time - 8 * 86400, current_time - 7 * 86400)
    ).values_list('user_id', flat=True)
    LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
        func_name="notify_tutorial", **{
            "job": "tutorial_day_7_autofill", "user_ids": list(users_7days),
        }
    )

    # 13 days
    users_13days = exclude_enterprise_users.exclude(
        pm_user_plan__start_period__isnull=True
    ).exclude(
        pm_user_plan__end_period__isnull=True
    ).annotate(
        plan_period=F('pm_user_plan__end_period') - F('pm_user_plan__start_period'),
        remain_period=F('pm_user_plan__end_period') - current_time
    ).filter(
        plan_period__lte=15 * 86400, remain_period__lte=86400, remain_period__gte=0
    ).values_list('user_id', flat=True)
    LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
        func_name="notify_tutorial", **{
            "job": "tutorial_day_13_trial_end", "user_ids": list(users_13days),
        }
    )

    # 20 days
    users_20days = exclude_enterprise_users.filter(
        creation_date__range=(current_time - 21 * 86400, current_time - 20 * 86400)
    ).values_list('user_id', flat=True)
    LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
        func_name="notify_tutorial", **{
            "job": "tutorial_day_20_refer_friend", "user_ids": list(users_20days),
        }
    )
