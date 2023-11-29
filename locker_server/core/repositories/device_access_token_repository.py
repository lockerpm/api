from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.device_access_token import DeviceAccessToken


class DeviceAccessTokenRepository(ABC):
    # ------------------------ List DeviceAccessToken resource ------------------- #
    @abstractmethod
    def list_sso_token_ids(self, device_ids: List, **filter_params) -> List[str]:
        pass

    # ------------------------ Get DeviceAccessToken resource --------------------- #
    @abstractmethod
    def get_device_access_token_by_id(self, device_access_token_id: str) -> Optional[DeviceAccessToken]:
        pass

    @abstractmethod
    def get_first_device_access_token_by_sso_ids(self, user_id: int,
                                                 sso_token_ids: List[str]) -> Optional[DeviceAccessToken]:
        pass

    # ------------------------ Create DeviceAccessToken resource --------------------- #
    @abstractmethod
    def fetch_device_access_token(self, device: Device, credential_key: str, renewal: bool = False,
                                  sso_token_id: str = None) -> DeviceAccessToken:
        pass

    # ------------------------ Update DeviceAccessToken resource --------------------- #

    # ------------------------ Delete DeviceAccessToken resource --------------------- #
    @abstractmethod
    def remove_devices_access_tokens(self, device_ids: List):
        pass
