from locker_server.core.entities.user.user import User


class Factor2Method(object):
    def __init__(self, factor2_method_id: int, method: str, is_activate: bool,
                 activate_code: str, code_expired_time: int, updated_time: int, user: User):
        self._factor2_method_id = factor2_method_id
        self._method = method
        self._is_activate = is_activate
        self._activate_code = activate_code
        self._code_expired_time = code_expired_time
        self._updated_time = updated_time
        self._user = user

    @property
    def factor2_method_id(self):
        return self._factor2_method_id

    @property
    def method(self):
        return self._method

    @property
    def is_activate(self):
        return self._is_activate

    @property
    def activate_code(self):
        return self._activate_code

    @property
    def code_expired_time(self):
        return self._code_expired_time

    @property
    def updated_time(self):
        return self._updated_time

    @property
    def user(self):
        return self._user
