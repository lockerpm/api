from typing import List, Optional

from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.device_access_token import DeviceAccessToken
from locker_server.core.exceptions.device_exception import DeviceDoesNotExistException
from locker_server.core.repositories.device_access_token_repository import DeviceAccessTokenRepository
from locker_server.core.repositories.device_repository import DeviceRepository


class DeviceService:
    """
    This class represents Use Cases related Device
    """

    def __init__(self, device_repository: DeviceRepository,
                 device_access_token_repository: DeviceAccessTokenRepository):
        self.device_repository = device_repository
        self.device_access_token_repository = device_access_token_repository

    def list_devices(self, **filter_params) -> List[Device]:
        return self.device_repository.list_devices(**filter_params)

    def list_fcm_ids(self, user_ids: List[int]) -> List[str]:
        return self.device_repository.get_fcm_ids_by_user_ids(user_ids=user_ids)

    def fetch_device_access_token(self, device: Device, credential_key: str, renewal: bool = True,
                                  sso_token_id: str = None) -> Optional[DeviceAccessToken]:
        access_token = self.device_access_token_repository.fetch_device_access_token(
            device=device, renewal=True, sso_token_id=sso_token_id,
            credential_key=credential_key
        )
        return access_token

    def get_device_by_identifier(self, user_id: int, device_identifier: str) -> Optional[Device]:
        device = self.device_repository.get_device_by_identifier(
            user_id=user_id,
            device_identifier=device_identifier
        )
        if not device:
            raise DeviceDoesNotExistException
        return device
