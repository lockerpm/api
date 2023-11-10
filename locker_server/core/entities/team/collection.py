from locker_server.core.entities.team.team import Team


class Collection(object):
    def __init__(self, collection_id: str, name: str, creation_date: float = None, revision_date: float = None,
                 external_id: str = None, is_default: bool = False, team: Team = None, hide_passwords: bool = False):
        self._collection_id = collection_id
        self._name = name
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._external_id = external_id
        self._is_default = is_default
        self._team = team
        self._hide_passwords = hide_passwords

    @property
    def collection_id(self):
        return self._collection_id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name_value):
        self._name = name_value

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date

    @revision_date.setter
    def revision_date(self, revision_date_value):
        self._revision_date = revision_date_value

    @property
    def external_id(self):
        return self._external_id

    @property
    def is_default(self):
        return self._is_default

    @property
    def team(self):
        return self._team

    @property
    def hide_passwords(self):
        return self._hide_passwords
