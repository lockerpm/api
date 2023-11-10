from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.team.group import Group


class GroupMember(object):
    def __init__(self, group_member_id: int, group: Group, member: TeamMember):
        self._group_member_id = group_member_id
        self._group = group
        self._member = member

    @property
    def group_member_id(self):
        return self._group_member_id

    @property
    def group(self):
        return self._group

    @property
    def member(self):
        return self._member
