from abc import ABC, abstractmethod
from typing import Optional, List

from cystack_models.models.users.users import User
from cystack_models.models.users.devices import Device
from cystack_models.models.users.device_access_tokens import DeviceAccessToken


class IDeviceRepository(ABC):
    @abstractmethod
    def fetch_device_access_token(self, device: Device, renewal: bool = False,
                                  sso_token_id: str = None) -> DeviceAccessToken:
        pass

    @abstractmethod
    def fetch_user_access_token(self, user: User, sso_token_id: str = None) -> Optional[DeviceAccessToken]:
        pass

    @abstractmethod
    def get_device_by_identifier(self, user: User, device_identifier: str) -> Optional[Device]:
        pass

    @abstractmethod
    def get_device_user(self, user: User):
        pass

    @abstractmethod
    def set_last_login(self, device: Device, last_login):
        pass

    @abstractmethod
    def get_devices_access_token(self, devices: List[Device]):
        pass

    @abstractmethod
    def remove_devices_access_token(self, devices: List[Device]):
        pass

    @abstractmethod
    def get_fcm_ids_by_user_ids(self, user_ids: List[int]):
        pass

    @abstractmethod
    def update_fcm_id(self, device: Device, fcm_id: str = None):
        pass
