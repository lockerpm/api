from locker_server.core.entities.user.user import User


class Folder(object):
    def __init__(self, folder_id: str, name: str, creation_date: float = None, revision_date: float = None,
                 user: User = None):
        self._folder_id = folder_id
        self._name = name
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._user = user

    @property
    def folder_id(self):
        return self._folder_id

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
    def user(self):
        return self._user
