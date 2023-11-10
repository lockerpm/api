from typing import Tuple, Dict, List, Optional

from locker_server.core.entities.user.device_access_token import DeviceAccessToken
from locker_server.core.exceptions.device_access_token_exception import DeviceAccessTokenDoesNotExistException
from locker_server.core.exceptions.user_exception import UserAuthFailedException
from locker_server.core.repositories.auth_repository import AuthRepository
from locker_server.core.repositories.device_access_token_repository import DeviceAccessTokenRepository
from locker_server.shared.utils.app import now


class AuthService:
    """
    This class represents Use Cases related authentication
    """

    def __init__(self, auth_repository: AuthRepository, device_access_token_repository: DeviceAccessTokenRepository):
        self.auth_repository = auth_repository
        self.device_access_token_repository = device_access_token_repository

    def decode_token(self, value: str, secret: str) -> Dict:
        """
        Decode a token string
        :param value: (str) token string
        :param secret: (str) Secret key to decode
        :return:
        """
        return self.auth_repository.decode_token(value=value, secret=secret)

    def check_device_access_token(self, access_token_value: str, secret: str,
                                  require_scopes: List[str] = None) -> Optional[DeviceAccessToken]:
        payload = self.decode_token(value=access_token_value, secret=secret)
        if not payload:
            raise UserAuthFailedException
        scopes = payload.get("scope", [])
        if require_scopes:
            for require_scope in require_scopes:
                if require_scope not in scopes:
                    raise UserAuthFailedException
        expired_time = payload.get("exp")
        if expired_time < now():
            raise UserAuthFailedException
        device_access_token_id = payload.get("jti")
        device_identifier = payload.get("device")
        client_id = payload.get("client_id")
        user_internal_id = payload.get("sub")

        device_access_token = self.device_access_token_repository.get_device_access_token_by_id(
            device_access_token_id=device_access_token_id
        )
        if not device_access_token:
            raise UserAuthFailedException
        device = device_access_token.device
        if device.device_identifier != device_identifier or device.client_id != client_id or \
                device.user.internal_id != user_internal_id:
            raise UserAuthFailedException
        return device_access_token

    def get_device_access_token_by_id(self, device_access_token_id: str) -> Optional[DeviceAccessToken]:
        device_access_token = self.device_access_token_repository.get_device_access_token_by_id(
            device_access_token_id=device_access_token_id
        )
        if not device_access_token:
            raise DeviceAccessTokenDoesNotExistException
        return device_access_token
