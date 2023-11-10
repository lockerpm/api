from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.member.member_role import MemberRole
from locker_server.core.entities.team.team import Team


class Group(object):
    def __init__(self, group_id: int, access_all: bool = True, creation_date: float = None, revision_date: float = None,
                 team: Team = None, enterprise_group: EnterpriseGroup = None, role: MemberRole = None):
        self._group_id = group_id
        self._access_all = access_all
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._team = team
        self._enterprise_group = enterprise_group
        self._role = role

    @property
    def group_id(self):
        return self._group_id

    @property
    def access_all(self):
        return self._access_all

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date

    @property
    def team(self):
        return self._team

    @property
    def enterprise_group(self):
        return self._enterprise_group

    @property
    def role(self):
        return self._role

    @property
    def name(self):
        return self.enterprise_group.name if self.enterprise_group else None
