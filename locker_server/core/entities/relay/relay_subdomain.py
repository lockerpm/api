from locker_server.core.entities.relay.relay_domain import RelayDomain
from locker_server.core.entities.user.user import User


class RelaySubdomain(object):
    def __init__(self, relay_subdomain_id: int, subdomain: str, created_time: float = None, is_deleted: bool = False,
                 user: User = None, domain: RelayDomain = None, num_alias=None, num_spam=None, num_forwarded=None):
        self._relay_subdomain_id = relay_subdomain_id
        self._subdomain = subdomain
        self._created_time = created_time
        self._is_deleted = is_deleted
        self._user = user
        self._domain = domain
        self._num_alias = num_alias
        self._num_spam = num_spam
        self._num_forwarded = num_forwarded

    @property
    def relay_subdomain_id(self):
        return self._relay_subdomain_id

    @property
    def subdomain(self):
        return self._subdomain

    @property
    def created_time(self):
        return self._created_time

    @property
    def is_deleted(self):
        return self._is_deleted

    @property
    def user(self):
        return self._user

    @property
    def domain(self):
        return self._domain

    @property
    def num_alias(self):
        return self._num_alias

    @num_alias.setter
    def num_alias(self, num_alias_value):
        self._num_alias = num_alias_value

    @property
    def num_spam(self):
        return self._num_spam

    @num_spam.setter
    def num_spam(self, num_spam_value):
        self._num_spam = num_spam_value

    @property
    def num_forwarded(self):
        return self._num_forwarded

    @num_forwarded.setter
    def num_forwarded(self, num_forwarded_value):
        self._num_forwarded = num_forwarded_value
