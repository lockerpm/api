from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.user import User


class DeviceRepository(ABC):
    # ------------------------ List Device resource ------------------- #
    @abstractmethod
    def list_user_devices(self, user_id: int, **filter_params) -> List[Device]:
        pass

    @abstractmethod
    def list_devices(self, **filter_params) -> List[Device]:
        pass

    # ------------------------ Get Device resource --------------------- #
    @abstractmethod
    def get_device_by_identifier(self, user_id: int, device_identifier: str) -> Optional[Device]:
        pass

    @abstractmethod
    def get_fcm_ids_by_user_ids(self, user_ids: List[int]) -> List[str]:
        pass

    @abstractmethod
    def is_active(self, device_id) -> bool:
        pass

    # ------------------------ Create Device resource --------------------- #
    @abstractmethod
    def retrieve_or_create(self, user_id: int, **data) -> Device:
        pass

    # ------------------------ Update Device resource --------------------- #
    @abstractmethod
    def set_last_login(self, device_id: int, last_login: float) -> Device:
        pass

    @abstractmethod
    def update_fcm_id(self, user_id: int, device_identifier: str, fcm_id: str) -> Device:
        pass

    # ------------------------ Delete Device resource --------------------- #
    @abstractmethod
    def destroy_device(self, device: Device) -> List[str]:
        pass
