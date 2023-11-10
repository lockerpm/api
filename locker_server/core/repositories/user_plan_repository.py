from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.user.user import User
from locker_server.core.entities.user_plan.pm_plan import PMPlan
from locker_server.core.entities.user_plan.pm_user_plan import PMUserPlan
from locker_server.core.entities.user_plan.pm_user_plan_family import PMUserPlanFamily
from locker_server.shared.constants.transactions import DURATION_MONTHLY, CURRENCY_USD, PLAN_TYPE_PM_FREE


class UserPlanRepository(ABC):
    # ------------------------ List PMUserPlan resource ------------------- #
    @abstractmethod
    def list_downgrade_plans(self) -> List[PMUserPlan]:
        pass

    @abstractmethod
    def list_expiring_plans(self) -> List[PMUserPlan]:
        pass

    @abstractmethod
    def list_expiring_enterprise_plans(self) -> List[PMUserPlan]:
        pass

    # ------------------------ Get PMUserPlan resource --------------------- #
    @abstractmethod
    def get_user_plan(self, user_id: int) -> Optional[PMUserPlan]:
        pass

    @abstractmethod
    def get_mobile_user_plan(self, pm_mobile_subscription: str) -> Optional[PMUserPlan]:
        pass

    @abstractmethod
    def get_default_enterprise(self, user_id: int, enterprise_name: str = None,
                               create_if_not_exist=False) -> Optional[Enterprise]:
        pass

    @abstractmethod
    def get_max_allow_cipher_type(self, user: User) -> Dict:
        pass

    @abstractmethod
    def is_in_family_plan(self, user_plan: PMUserPlan) -> bool:
        pass

    @abstractmethod
    def is_family_member(self, user_id: int) -> bool:
        pass

    @abstractmethod
    def get_family_members(self, user_id: int) -> Dict:
        pass

    @abstractmethod
    def get_family_member(self, owner_user_id: int, family_member_id: int) -> Optional[PMUserPlanFamily]:
        pass

    @abstractmethod
    def count_family_members(self, user_id: int) -> int:
        pass

    @abstractmethod
    def calc_update_price(self, current_plan: PMUserPlan, new_plan: PMPlan, new_duration: str, new_quantity: int = 1,
                          currency: str = CURRENCY_USD, promo_code: str = None, allow_trial: bool = True,
                          utm_source: str = None) -> Dict:
        pass

    @abstractmethod
    def calc_payment_public(self, new_plan: PMPlan, new_duration: str, new_quantity: int, currency: str = CURRENCY_USD,
                            promo_code: str = None, allow_trial: bool = True, utm_source: str = None,
                            ) -> Dict:
        pass

    @abstractmethod
    def calc_lifetime_payment_public(self, new_plan: PMPlan, currency: str = CURRENCY_USD, promo_code: str = None,
                                     user: User = None):
        pass

    @abstractmethod
    def is_update_personal_to_enterprise(self, current_plan: PMUserPlan, new_plan_alias: str) -> bool:
        pass

    # ------------------------ Create PMUserPlan resource --------------------- #
    @abstractmethod
    def add_to_family_sharing(self, family_user_plan_id: int, user_id: int = None,
                              email: str = None) -> Optional[PMUserPlan]:
        pass

    # ------------------------ Update PMUserPlan resource --------------------- #
    @abstractmethod
    def update_plan(self, user_id: int, plan_type_alias: str, duration: str = DURATION_MONTHLY, scope: str = None,
                    **kwargs):
        pass

    @abstractmethod
    def set_personal_trial_applied(self, user_id: int, applied: bool = True, platform: str = None):
        pass

    @abstractmethod
    def set_enterprise_trial_applied(self, user_id: int, applied: bool = True, platform: str = None):
        pass

    @abstractmethod
    def set_default_payment_method(self, user_id: int, payment_method: str):
        pass

    @abstractmethod
    def upgrade_member_family_plan(self, user: User) -> Optional[User]:
        pass

    @abstractmethod
    def update_user_plan_by_id(self, user_plan_id: str, user_plan_update_data) -> Optional[PMUserPlan]:
        pass

    # ------------------------ Delete PMUserPlan resource --------------------- #
    @abstractmethod
    def cancel_plan(self, user: User, immediately=False, **kwargs):
        pass

    @abstractmethod
    def delete_family_member(self, family_member_id: int):
        pass
