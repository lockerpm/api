from locker_server.api_orm.abstracts.user_plans.plan_types import AbstractPlanTypeORM


class PlanTypeORM(AbstractPlanTypeORM):
    class Meta(AbstractPlanTypeORM.Meta):
        swappable = 'LS_PLAN_TYPE_MODEL'
        db_table = 'cs_plan_types'
