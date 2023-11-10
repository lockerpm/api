from locker_server.core.entities.quick_share.quick_share import QuickShare


class QuickShareEmail(object):
    def __init__(self, quick_share_email_id: str, creation_date: float = None, email: str = None, code: str = None,
                 code_expired_time: float = None, max_access_count: int = None, access_count: int = 0,
                 quick_share: QuickShare = None):
        self._quick_share_email_id = quick_share_email_id
        self._creation_date = creation_date
        self._email = email
        self._code = code
        self._code_expired_time = code_expired_time
        self._max_access_count = max_access_count
        self._access_count = access_count
        self._quick_share = quick_share

    @property
    def quick_share_email_id(self):
        return self._quick_share_email_id

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def email(self):
        return self._email

    @property
    def code(self):
        return self._code

    @property
    def code_expired_time(self):
        return self._code_expired_time

    @property
    def max_access_count(self):
        return self._max_access_count

    @property
    def access_count(self):
        return self._access_count

    @property
    def quick_share(self):
        return self._quick_share
