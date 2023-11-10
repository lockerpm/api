from locker_server.core.entities.enterprise.domain.domain import Domain
from locker_server.core.entities.enterprise.domain.ownership import Ownership


class DomainOwnership(object):
    def __init__(self, domain_ownership_id: int, key: str, value: str, verification: bool = False,
                 domain: Domain = None, ownership: Ownership = None):
        self._domain_ownership_id = domain_ownership_id
        self._key = key
        self._value = value
        self._verification = verification
        self._domain = domain
        self._ownership = ownership

    @property
    def domain_ownership_id(self):
        return self._domain_ownership_id

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value

    @property
    def verification(self):
        return self._verification

    @property
    def domain(self):
        return self._domain

    @property
    def ownership(self):
        return self._ownership
