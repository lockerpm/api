from locker_server.api_orm.abstracts.user_plans.pm_plans import AbstractPMPlanORM


class PMPlanORM(AbstractPMPlanORM):
    class Meta(AbstractPMPlanORM.Meta):
        swappable = 'LS_PLAN_MODEL'
        db_table = 'cs_pm_plans'
