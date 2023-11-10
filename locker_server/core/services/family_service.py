from typing import Optional, List, Dict

from locker_server.core.entities.user_plan.pm_user_plan import PMUserPlan
from locker_server.core.exceptions.user_plan_exception import *
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.core.repositories.user_repository import UserRepository


class FamilyService:
    """
    This class represents Use Cases related User
    """

    def __init__(self, user_repository: UserRepository,
                 user_plan_repository: UserPlanRepository):
        self.user_repository = user_repository
        self.user_plan_repository = user_plan_repository

    def is_in_family_plan(self, user_plan: PMUserPlan) -> bool:
        return self.user_plan_repository.is_in_family_plan(user_plan=user_plan)

    def list_family_members(self, user_id: int) -> Dict:
        return self.user_plan_repository.get_family_members(user_id=user_id)

    def create_multiple_family_members(self, user_id: int, family_members: List[Dict]):
        current_family_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
        pm_plan = current_family_plan.pm_plan

        # Check max number is reached?
        if len(family_members) > pm_plan.max_number - self.user_plan_repository.count_family_members(user_id=user_id):
            raise MaxUserPlanFamilyReachedException

        for family_member in family_members:
            user_id = family_member.get("user_id")
            email = family_member.get("email")
            if user_id:
                user = self.user_repository.get_user_by_id(user_id=user_id)
                if not user:
                    continue
                if not user.activated:
                    continue
                current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
                if current_plan.pm_plan.is_family_plan or current_plan.pm_plan.is_team_plan:
                    raise UserIsInOtherFamilyException(email=email)

                # current_plan = user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
                # if current_plan.get_plan_obj().is_family_plan or current_plan.get_plan_obj().is_team_plan:
                #     raise serializers.ValidationError(detail={
                #         "family_members": ["The user {} is in other family plan".format(email)]
                #     })

        for family_member in family_members:
            email = family_member.get("email")
            user_id = family_member.get("user_id")
            self.user_plan_repository.add_to_family_sharing(
                family_user_plan_id=current_family_plan.user.user_id, user_id=user_id, email=email
            )

    def destroy_family_member(self, user_id: int, family_member_id: int):
        family_member = self.user_plan_repository.get_family_member(
            owner_user_id=user_id, family_member_id=family_member_id
        )
        if not family_member:
            raise UserPlanFamilyDoesNotExistException
        if family_member.user.user_id == user_id:
            raise UserPlanFamilyDoesNotExistException
        # Downgrade the plan of the member user
        family_user_id, family_email = self.user_plan_repository.delete_family_member(family_member_id=family_member_id)
        return family_user_id, family_email
