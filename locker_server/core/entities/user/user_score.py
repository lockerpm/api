from locker_server.core.entities.user.user import User


class UserScore(object):
    def __init__(self, user: User, cipher0: float = 0, cipher1: float = 0, cipher2: float = 0, cipher3: float = 0,
                 cipher4: float = 0, cipher5: float = 0, cipher6: float = 0, cipher7: float = 0):
        self._user = user
        self._cipher0 = cipher0
        self._cipher1 = cipher1
        self._cipher2 = cipher2
        self._cipher3 = cipher3
        self._cipher4 = cipher4
        self._cipher5 = cipher5
        self._cipher6 = cipher6
        self._cipher7 = cipher7

    @property
    def user(self):
        return self._user

    @property
    def cipher0(self):
        return self._cipher0

    @property
    def cipher1(self):
        return self._cipher1

    @property
    def cipher2(self):
        return self._cipher2

    @property
    def cipher3(self):
        return self._cipher3

    @property
    def cipher4(self):
        return self._cipher4

    @property
    def cipher5(self):
        return self._cipher5

    @property
    def cipher6(self):
        return self._cipher6

    @property
    def cipher7(self):
        return self._cipher7
