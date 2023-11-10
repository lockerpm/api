from typing import List

from locker_server.core.entities.cipher.cipher import Cipher


class QuickShare(object):
    def __init__(self, quick_share_id: str, cipher: Cipher, access_id: str = None, creation_date: float = None,
                 revision_date: float = None, deleted_date: float = None, quick_share_type: int = None, data: str = None,
                 key: str = None, password: str = None, each_email_access_count: int = None,
                 max_access_count: int = None, access_count: int = 0, expiration_date: float = None,
                 disabled: bool = False, is_public: bool= True, require_otp: bool = True, emails: List = None):
        self._quick_share_id = quick_share_id
        self._cipher = cipher
        self._access_id = access_id
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._deleted_date = deleted_date
        self._quick_share_type = quick_share_type
        self._data = data
        self._key = key
        self._password = password
        self._each_email_access_count = each_email_access_count
        self._max_access_count = max_access_count
        self._access_count = access_count
        self._expiration_date = expiration_date
        self._disabled = disabled
        self._is_public = is_public
        self._require_otp = require_otp
        self._emails = emails or []

    @property
    def quick_share_id(self):
        return self._quick_share_id

    @property
    def cipher(self):
        return self._cipher

    @property
    def access_id(self):
        return self._access_id

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
    def quick_share_type(self):
        return self._quick_share_type

    @property
    def data(self):
        return self._data

    @property
    def key(self):
        return self._key

    @property
    def password(self):
        return self._password

    @property
    def each_email_access_count(self):
        return self._each_email_access_count

    @property
    def max_access_count(self):
        return self._max_access_count

    @property
    def access_count(self):
        return self._access_count

    @property
    def expiration_date(self):
        return self._expiration_date

    @property
    def disabled(self):
        return self._disabled

    @property
    def is_public(self):
        return self._is_public

    @property
    def require_otp(self):
        return self._require_otp

    @property
    def emails(self):
        return self._emails
