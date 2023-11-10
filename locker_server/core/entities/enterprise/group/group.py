from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.user.user import User


class EnterpriseGroup(object):
    def __init__(self, enterprise_group_id: str, name: str, creation_date: float = None, revision_date: float = None,
                 created_by: User = None, enterprise: Enterprise = None):
        self._enterprise_group_id = enterprise_group_id
        self._name = name
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._created_by = created_by
        self._enterprise = enterprise

    @property
    def enterprise_group_id(self):
        return self._enterprise_group_id

    @property
    def name(self):
        return self._name

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date

    @property
    def created_by(self):
        return self._created_by

    @property
    def enterprise(self):
        return self._enterprise

