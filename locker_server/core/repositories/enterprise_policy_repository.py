from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.policy.policy import EnterprisePolicy
from locker_server.core.entities.enterprise.policy.policy_2fa import Policy2FA
from locker_server.core.entities.enterprise.policy.policy_failed_login import PolicyFailedLogin
from locker_server.core.entities.enterprise.policy.policy_master_password import PolicyMasterPassword
from locker_server.core.entities.enterprise.policy.policy_password import PolicyPassword
from locker_server.core.entities.enterprise.policy.policy_passwordless import PolicyPasswordless
from locker_server.core.entities.event.event import Event
from locker_server.core.entities.user.user import User


class EnterprisePolicyRepository(ABC):
    # ------------------------ List EnterprisePolicy resource ------------------- #
    @abstractmethod
    def list_policies_by_user(self, user_id: int) -> List[EnterprisePolicy]:
        pass

    @abstractmethod
    def list_2fa_policy(self, enterprise_ids: List[str], enabled: bool = True) -> List[Policy2FA]:
        pass

    @abstractmethod
    def list_enterprise_policies(self, enterprise_id: str) -> List[EnterprisePolicy]:
        pass

    # ------------------------ Get EnterprisePolicy resource --------------------- #
    @abstractmethod
    def get_block_failed_login_policy(self, user_id: int) -> Optional[PolicyFailedLogin]:
        pass

    @abstractmethod
    def get_enterprise_2fa_policy(self, enterprise_id: str) -> Optional[Policy2FA]:
        pass

    @abstractmethod
    def get_policy_by_type(self, enterprise_id: str, policy_type: str) -> Optional[EnterprisePolicy]:
        pass

    @abstractmethod
    def get_policy_password_requirement(self, policy_id: str) -> Optional[PolicyPassword]:
        pass

    @abstractmethod
    def get_policy_master_password_requirement(self, policy_id: str) -> Optional[PolicyMasterPassword]:
        pass

    @abstractmethod
    def get_policy_block_failed_login(self, policy_id: str) -> Optional[PolicyFailedLogin]:
        pass

    @abstractmethod
    def get_policy_type_passwordless(self, policy_id: str) -> Optional[PolicyPasswordless]:
        pass

    @abstractmethod
    def get_policy_2fa(self, policy_id: str) -> Optional[Policy2FA]:
        pass

    # ------------------------ Create EnterprisePolicy resource --------------------- #
    @abstractmethod
    def create_policy(self, policy_create_data) -> EnterprisePolicy:
        pass

    # ------------------------ Update EnterprisePolicy resource --------------------- #
    @abstractmethod
    def update_policy_password_requirement(self, policy_id: str, update_data) -> Optional[PolicyPassword]:
        pass

    @abstractmethod
    def update_policy_master_password_requirement(self, policy_id: str, update_data) -> Optional[PolicyMasterPassword]:
        pass

    @abstractmethod
    def update_policy_block_failed_login(self, policy_id: str, update_data) -> Optional[PolicyFailedLogin]:
        pass

    @abstractmethod
    def update_policy_type_passwordless(self, policy_id: str, update_data) -> Optional[PolicyPasswordless]:
        pass

    @abstractmethod
    def update_policy_2fa(self, policy_id: str, update_data) -> Optional[Policy2FA]:
        pass

    # ------------------------ Delete EnterprisePolicy resource --------------------- #
