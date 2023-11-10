from locker_server.core.entities.enterprise.domain.domain import Domain
from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.member.enterprise_member_role import EnterpriseMemberRole
from locker_server.core.entities.user.user import User
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED


class EnterpriseMember(object):
    def __init__(self, enterprise_member_id: str, access_time: float = None, is_default: bool = False,
                 is_primary: bool = False, is_activated: bool = False, status: str = E_MEMBER_STATUS_CONFIRMED,
                 email: str = None, token_invitation: str = None, user: User = None, enterprise: Enterprise = None,
                 role: EnterpriseMemberRole = None, domain: Domain = None):
        self._enterprise_member_id = enterprise_member_id
        self._access_time = access_time
        self._is_default = is_default
        self._is_primary = is_primary
        self._is_activated = is_activated
        self._status = status
        self._email = email
        self._token_invitation = token_invitation
        self._user = user
        self._enterprise = enterprise
        self._role = role
        self._domain = domain

    @property
    def enterprise_member_id(self):
        return self._enterprise_member_id

    @property
    def access_time(self):
        return self._access_time

    @property
    def is_default(self):
        return self._is_default

    @property
    def is_primary(self):
        return self._is_primary

    @property
    def is_activated(self):
        return self._is_activated

    @property
    def status(self):
        return self._status

    @property
    def email(self):
        return self._email

    @property
    def token_invitation(self):
        return self._token_invitation

    @property
    def user(self):
        return self._user

    @property
    def enterprise(self):
        return self._enterprise

    @property
    def role(self):
        return self._role

    @property
    def domain(self):
        return self._domain
