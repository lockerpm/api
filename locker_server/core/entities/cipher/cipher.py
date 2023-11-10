from locker_server.core.entities.team.team import Team
from locker_server.core.entities.user.user import User


class Cipher(object):
    def __init__(self, cipher_id: str, creation_date: float = None, revision_date: float = None,
                 deleted_date: float = None, last_use_date: float = None, num_use: int = 0, reprompt: int = 0,
                 score: float = 0,  cipher_type: int = None, data: str = None, favorites: str = "", folders: str = "",
                 view_password: bool = True, user: User = None, created_by: User = None, team: Team = None):
        self._cipher_id = cipher_id
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._deleted_date = deleted_date
        self._last_use_date = last_use_date
        self._num_use = num_use
        self._reprompt = reprompt
        self._score = score
        self._cipher_type = cipher_type
        self._data = data
        self._favorites = favorites
        self._folders = folders
        self._view_password = view_password
        self._collection_ids = []
        self._user = user
        self._created_by = created_by
        self._team = team

    @property
    def cipher_id(self):
        return self._cipher_id

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date

    @property
    def deleted_date(self):
        return self._deleted_date

    @property
    def last_use_date(self):
        return self._last_use_date

    @property
    def num_use(self):
        return self._num_use

    @property
    def reprompt(self):
        return self._reprompt

    @property
    def score(self):
        return self._score

    @property
    def cipher_type(self):
        return self._cipher_type

    @property
    def data(self):
        return self._data

    @property
    def favorites(self):
        return self._favorites

    @property
    def folders(self):
        return self._folders

    @property
    def user(self):
        return self._user

    @property
    def team(self):
        return self._team

    @property
    def created_by(self):
        return self._created_by

    @property
    def view_password(self):
        return self._view_password

    @view_password.setter
    def view_password(self, view_password_value):
        self._view_password = view_password_value

    @property
    def collection_ids(self):
        return self._collection_ids

    @collection_ids.setter
    def collection_ids(self, collection_ids_value):
        self._collection_ids = collection_ids_value
