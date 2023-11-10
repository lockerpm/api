from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.emergency_access.emergency_access import EmergencyAccess
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.user import User


class EmergencyAccessRepository(ABC):
    # ------------------------ List EmergencyAccess resource ------------------- #
    @abstractmethod
    def list_by_grantor_id(self, grantor_id: int) -> List[EmergencyAccess]:
        pass

    @abstractmethod
    def list_by_grantee_id(self, grantee_id: int) -> List[EmergencyAccess]:
        pass

    # ------------------------ Get EmergencyAccess resource --------------------- #
    @abstractmethod
    def get_by_id(self, emergency_access_id: str) -> Optional[EmergencyAccess]:
        pass

    @abstractmethod
    def check_emergency_existed(self, grantor_id: int, emergency_access_type: str,
                                grantee_id: int = None, email: str = None) -> bool:
        pass

    # ------------------------ Create EmergencyAccess resource --------------------- #
    @abstractmethod
    def invite_emergency_access(self, grantor_id: int, emergency_access_type: str, wait_time_days: int, key: str = None,
                                grantee_id: int = None, email: str = None) -> Optional[EmergencyAccess]:
        pass

    # ------------------------ Update EmergencyAccess resource --------------------- #
    @abstractmethod
    def accept_emergency_access(self, emergency_access: EmergencyAccess) -> EmergencyAccess:
        pass

    @abstractmethod
    def confirm_emergency_access(self, emergency_access: EmergencyAccess, key_encrypted: str) -> EmergencyAccess:
        pass

    @abstractmethod
    def initiate_emergency_access(self, emergency_access: EmergencyAccess):
        pass

    @abstractmethod
    def reject_emergency_access(self, emergency_access: EmergencyAccess):
        pass

    @abstractmethod
    def approve_emergency_access(self, emergency_access: EmergencyAccess):
        pass

    @abstractmethod
    def auto_approve_emergency_accesses(self):
        pass

    # ------------------------ Delete EmergencyAccess resource --------------------- #
    @abstractmethod
    def destroy_emergency_access(self, emergency_access_id: str):
        pass
