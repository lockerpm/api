

class Team(object):
    def __init__(self, team_id: str, name: str = None, description: str = '', creation_date: float = None,
                 revision_date: float = None, locked: bool = False, business_name: str = None,
                 key: str = None, default_collection_name: str = None, public_key: str = None, private_key: str = None,
                 personal_share: bool = True):
        self._team_id = team_id
        self._name = name
        self._description = description
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._locked = locked
        self._business_name = business_name
        self._key = key
        self._default_collection_name = default_collection_name
        self._public_key = public_key
        self._private_key = private_key
        self._personal_share = personal_share

    @property
    def team_id(self):
        return self._team_id

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date

    @property
    def locked(self):
        return self._locked

    @property
    def business_name(self):
        return self._business_name

    @property
    def key(self):
        return self._key

    @property
    def default_collection_name(self):
        return self._default_collection_name

    @property
    def public_key(self):
        return self._public_key

    @property
    def private_key(self):
        return self._private_key

    @property
    def personal_share(self):
        return self._personal_share
