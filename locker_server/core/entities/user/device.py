from locker_server.core.entities.user.user import User


class Device(object):
    def __init__(self, device_id: int, created_time: float = None, refresh_token: str = None, token_type: str = None,
                 scope: str = None, client_id: str = None, device_name: str = None, device_type: str = None,
                 device_identifier: str = None, fcm_id: str = None, last_login: float = None, os: str = "",
                 browser: str = "", user: User = None, is_active: bool = False):
        self._device_id = device_id
        self._created_time = created_time
        self._refresh_token = refresh_token
        self._token_type = token_type
        self._scope = scope
        self._client_id = client_id
        self._device_name = device_name
        self._device_type = device_type
        self._device_identifier = device_identifier
        self._fcm_id = fcm_id
        self._last_login = last_login
        self._os = os
        self._browser = browser
        self._user = user
        self._is_active = is_active

    @property
    def device_id(self):
        return self._device_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def refresh_token(self):
        return self._refresh_token

    @property
    def token_type(self):
        return self._token_type

    @property
    def scope(self):
        return self._scope

    @property
    def client_id(self):
        return self._client_id

    @property
    def device_name(self):
        return self._device_name

    @property
    def device_type(self):
        return self._device_type

    @property
    def device_identifier(self):
        return self._device_identifier

    @property
    def fcm_id(self):
        return self._fcm_id

    @property
    def last_login(self):
        return self._last_login

    @property
    def os(self):
        return self._os

    @property
    def browser(self):
        return self._browser

    @property
    def user(self):
        return self._user

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, is_active_value):
        self._is_active = is_active_value
