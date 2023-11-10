from locker_server.core.entities.user.device import Device


class DeviceAccessToken(object):
    def __init__(self, device_access_token_id: int, access_token: str, expired_time: float = None,
                 grant_type: str = "", sso_token_id: str = None, device: Device = None):
        self._device_access_token_id = device_access_token_id
        self._access_token = access_token
        self._expired_time = expired_time
        self._grant_type = grant_type
        self._sso_token_id = sso_token_id
        self._device = device

    @property
    def device_access_token_id(self):
        return self._device_access_token_id

    @property
    def access_token(self):
        return self._access_token

    @property
    def expired_time(self):
        return self._expired_time

    @property
    def grant_type(self):
        return self._grant_type

    @property
    def sso_token_id(self):
        return self._sso_token_id

    @property
    def device(self):
        return self._device
