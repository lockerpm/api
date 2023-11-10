from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_plan_model
from locker_server.core.entities.user_plan.pm_plan import PMPlan
from locker_server.core.repositories.plan_repository import PlanRepository


PMPlanORM = get_plan_model()
ModelParser = get_model_parser()


class PlanORMRepository(PlanRepository):
    # ------------------------ List PMPlan resource ------------------- #
    def list_plans(self, **filter_params) -> List[PMPlan]:
        plans_orm = PMPlanORM.objects.filter().order_by('id')
        is_team_plan_param = filter_params.get("is_team_plan")
        exclude_alias_param = filter_params.get("exclude_alias")
        if is_team_plan_param is not None:
            plans_orm = plans_orm.filter(is_team_plan=is_team_plan_param)
        if exclude_alias_param:
            plans_orm = plans_orm.exclude(alias__in=exclude_alias_param)
        return [ModelParser.user_plan_parser().parse_plan(plan_orm=plan_orm) for plan_orm in plans_orm]

    # ------------------------ Get PMPlan resource --------------------- #
    def get_plan_by_alias(self, alias: str) -> Optional[PMPlan]:
        try:
            plan_orm = PMPlanORM.objects.get(alias=alias)
            return ModelParser.user_plan_parser().parse_plan(plan_orm=plan_orm)
        except PMPlanORM.DoesNotExist:
            return None

    # ------------------------ Create PMPlan resource --------------------- #

    # ------------------------ Update PMPlan resource --------------------- #

    # ------------------------ Delete PMPlan resource --------------------- #

