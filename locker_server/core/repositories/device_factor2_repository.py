from typing import Optional, List, Dict
from abc import ABC, abstractmethod

from locker_server.core.entities.factor2.device_factor2 import DeviceFactor2


class DeviceFactor2Repository(ABC):
    # ------------------------ List DeviceFactor2 resource ------------------- #
    @abstractmethod
    def list_user_device_factor2s(self, user_id: int, **filter_params) -> List[DeviceFactor2]:
        pass

    # ------------------------ Get DeviceFactor2 resource --------------------- #
    @abstractmethod
    def get_device_factor2_by_id(self, device_factor2_id: str) -> Optional[DeviceFactor2]:
        pass

    @abstractmethod
    def get_device_factor2_by_method(self, user_id: int, method: str) -> DeviceFactor2:
        pass

    # ------------------------ Create DeviceFactor2 resource --------------------- #
    @abstractmethod
    def create_device_factor2(self, device_factor2_create_data: Dict) -> DeviceFactor2:
        pass

    # ------------------------ Update DeviceFactor2 resource --------------------- #

    # ------------------------ Delete DeviceFactor2 resource --------------------- #
