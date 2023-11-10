from locker_server.core.entities.user.user import User


class ExcludeDomain(object):
    def __init__(self, exclude_domain_id: str, user: User, created_time: float = None, domain: str = None):
        self._exclude_domain_id = exclude_domain_id
        self._user = user
        self._created_time = created_time
        self._domain = domain

    @property
    def exclude_domain_id(self):
        return self._exclude_domain_id

    @property
    def user(self):
        return self._user

    @property
    def created_time(self):
        return self._created_time

    @property
    def domain(self):
        return self._domain
