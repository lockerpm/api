from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember


class EnterpriseGroupMember(object):
    def __init__(self, enterprise_group_member_id: int, group: EnterpriseGroup, member: EnterpriseMember):
        self._enterprise_group_member_id = enterprise_group_member_id
        self._group = group
        self._member = member

    @property
    def enterprise_group_member_id(self):
        return self._enterprise_group_member_id

    @property
    def group(self):
        return self._group

    @property
    def member(self):
        return self._member
