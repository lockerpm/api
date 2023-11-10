from hashlib import sha256

from locker_server.core.entities.relay.relay_domain import RelayDomain
from locker_server.core.entities.relay.relay_subdomain import RelaySubdomain
from locker_server.core.entities.user.user import User


class RelayAddress(object):
    def __init__(self, relay_address_id: int, user: User = None, address: str = None, subdomain: RelaySubdomain = None,
                 domain: RelayDomain = None, enabled: bool = True, block_spam: bool = False, description: str = "",
                 created_time: float = None, updated_time: float = None, num_forwarded: int = 0, num_blocked: int = 0,
                 num_replied: int = 0, num_spam: int = 0):
        self._relay_address_id = relay_address_id
        self._user = user
        self._address = address
        self._subdomain = subdomain
        self._domain = domain
        self._enabled = enabled
        self._block_spam = block_spam
        self._description = description
        self._created_time = created_time
        self._updated_time = updated_time
        self._num_forwarded = num_forwarded
        self._num_blocked = num_blocked
        self._num_replied = num_replied
        self._num_spam = num_spam

    @property
    def relay_address_id(self):
        return self._relay_address_id

    @property
    def user(self):
        return self._user

    @property
    def address(self):
        return self._address

    @property
    def subdomain(self):
        return self._subdomain

    @property
    def domain(self):
        return self._domain

    @property
    def enabled(self):
        return self._enabled

    @property
    def block_spam(self):
        return self._block_spam

    @property
    def description(self):
        return self._description

    @property
    def created_time(self):
        return self._created_time

    @property
    def updated_time(self):
        return self._updated_time

    @property
    def num_forwarded(self):
        return self._num_forwarded

    @property
    def num_blocked(self):
        return self._num_blocked

    @property
    def num_replied(self):
        return self._num_replied

    @property
    def num_spam(self):
        return self._num_spam

    @property
    def full_address(self):
        if self.subdomain:
            return f"{self.address}@{self.subdomain.subdomain}.{self.domain.relay_domain_id}"
        return f"{self.address}@{self.domain.relay_domain_id}"

    @classmethod
    def hash_address(cls, address, domain):
        return sha256(f"{address}@{domain}".encode("utf-8")).hexdigest()
