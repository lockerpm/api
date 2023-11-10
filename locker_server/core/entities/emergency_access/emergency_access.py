from locker_server.core.entities.user.user import User
from locker_server.shared.constants.emergency_access import EMERGENCY_ACCESS_STATUS_INVITED


class EmergencyAccess(object):
    def __init__(self, emergency_access_id: str, creation_date: int = None, revision_date: float = None,
                 last_notification_date: float = None, recovery_initiated_date: float = None,
                 status: str = EMERGENCY_ACCESS_STATUS_INVITED, emergency_access_type: str = None,
                 wait_time_days: int = 7, key_encrypted: str = None, email: str = None,
                 grantee: User = None, grantor: User = None):
        self._emergency_access_id = emergency_access_id
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._last_notification_date = last_notification_date
        self._recovery_initiated_date = recovery_initiated_date
        self._status = status
        self._emergency_access_type = emergency_access_type
        self._wait_time_days = wait_time_days
        self._key_encrypted = key_encrypted
        self._email = email
        self._grantee = grantee
        self._grantor = grantor

    @property
    def emergency_access_id(self):
        return self._emergency_access_id

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date

    @property
    def last_notification_date(self):
        return self._last_notification_date

    @property
    def recovery_initiated_date(self):
        return self._recovery_initiated_date

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status_value):
        self._status = status_value

    @property
    def emergency_access_type(self):
        return self._emergency_access_type

    @property
    def wait_time_days(self):
        return self._wait_time_days

    @wait_time_days.setter
    def wait_time_days(self, wait_time_days_value):
        self._wait_time_days = wait_time_days_value

    @property
    def key_encrypted(self):
        return self._key_encrypted

    @key_encrypted.setter
    def key_encrypted(self, key_encrypted_value):
        self._key_encrypted = key_encrypted_value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email_value):
        self._email = email_value

    @property
    def grantee(self):
        return self._grantee

    @property
    def grantor(self):
        return self._grantor
