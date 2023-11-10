from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.team.collection import Collection


class CollectionMember(object):
    def __init__(self, collection_member_id: int, collection: Collection = None, member: TeamMember = None,
                 read_only: bool = False, hide_passwords: bool = False):
        self._collection_member_id = collection_member_id
        self._collection = collection
        self._member = member
        self._read_only = read_only
        self._hide_passwords = hide_passwords

    @property
    def collection_member_id(self):
        return self._collection_member_id

    @property
    def collection(self):
        return self._collection

    @property
    def member(self):
        return self._member

    @property
    def read_only(self):
        return self._read_only

    @property
    def hide_passwords(self):
        return self._hide_passwords
