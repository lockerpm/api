from abc import ABC, abstractmethod

from cystack_models.models.users.users import User
from cystack_models.models.emergency_access.emergency_access import EmergencyAccess


class IEmergencyAccessRepository(ABC):
    @abstractmethod
    def get_by_id(self, emergency_access_id):
        pass

    @abstractmethod
    def get_multiple_by_grantor(self, grantor: User):
        pass

    @abstractmethod
    def get_multiple_by_grantee(self, grantee: User):
        pass

    @abstractmethod
    def delete_emergency_access(self, emergency_access: EmergencyAccess, user_id):
        pass

    @abstractmethod
    def invite_emergency_access(self, access_type, wait_time_days, grantor, grantee=None, email=None):
        pass

    @abstractmethod
    def accept_emergency_access(self, emergency_access: EmergencyAccess):
        pass

    @abstractmethod
    def confirm_emergency_access(self, emergency_access: EmergencyAccess, key_encrypted: str):
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
