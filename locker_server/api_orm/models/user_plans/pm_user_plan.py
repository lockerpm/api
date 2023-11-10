from locker_server.api_orm.abstracts.user_plans.pm_user_plan import AbstractPMUserPlanORM
from locker_server.api_orm.models import PMPlanORM
from locker_server.shared.constants.transactions import PLAN_TYPE_PM_FREE, DURATION_MONTHLY


class PMUserPlanORM(AbstractPMUserPlanORM):
    class Meta(AbstractPMUserPlanORM.Meta):
        swappable = 'LS_USER_PLAN_MODEL'
        db_table = 'cs_pm_user_plan'

    @classmethod
    def update_or_create(cls, user, pm_plan_alias=PLAN_TYPE_PM_FREE, duration=DURATION_MONTHLY):
        """
        Create plan object
        :param user: (obj) User object
        :param pm_plan_alias: (str) PM plan alias
        :param duration: (str) duration of this plan
        :return:
        """
        plan_type = PMPlanORM.objects.get(alias=pm_plan_alias)
        user_plan, is_created = PMUserPlanORM.objects.update_or_create(
            user=user, defaults={
                "pm_plan": plan_type,
                "duration": duration,
                "user": user
            }
        )
        return user_plan
