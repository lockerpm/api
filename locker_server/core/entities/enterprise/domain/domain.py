from locker_server.core.entities.enterprise.enterprise import Enterprise


class Domain(object):
    def __init__(self, domain_id: int, created_time: float = None, updated_time: float = None, domain: str = None,
                 root_domain: str = None, verification: bool = False, auto_approve: float = False,
                 is_notify_failed: bool = False, enterprise: Enterprise = None):
        self._domain_id = domain_id
        self._created_time = created_time
        self._updated_time = updated_time
        self._domain = domain
        self._root_domain = root_domain
        self._verification = verification
        self._auto_approve = auto_approve
        self._is_notify_failed = is_notify_failed
        self._enterprise = enterprise

    @property
    def domain_id(self):
        return self._domain_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def updated_time(self):
        return self._updated_time

    @property
    def domain(self):
        return self._domain

    @property
    def root_domain(self):
        return self._root_domain

    @property
    def verification(self):
        return self._verification

    @property
    def auto_approve(self):
        return self._auto_approve

    @property
    def is_notify_failed(self):
        return self._is_notify_failed

    @property
    def enterprise(self):
        return self._enterprise
