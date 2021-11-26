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
