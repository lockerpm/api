from locker_server.core.entities.member.member_role import MemberRole
from locker_server.core.entities.team.team import Team
from locker_server.core.entities.user.user import User
from locker_server.shared.constants.members import PM_MEMBER_STATUS_CONFIRMED


class TeamMember(object):
    def __init__(self, team_member_id: str, external_id: str = None, access_time: int = None, is_default: bool = False,
                 is_primary: bool = False, is_added_by_group: bool = False, hide_passwords: bool = False,
                 key: str = None, reset_password_key: str = None, status: str = PM_MEMBER_STATUS_CONFIRMED,
                 email: str = None, token_invitation: str = None, user: User = None, team: Team = None,
                 role: MemberRole = None):
        self._team_member_id = team_member_id
        self._external_id = external_id
        self._access_time = access_time
        self._is_default = is_default
        self._is_primary = is_primary
        self._is_added_by_group = is_added_by_group
        self._hide_passwords = hide_passwords
        self._key = key
        self._reset_password_key = reset_password_key
        self._status = status
        self._email = email
        self._token_invitation = token_invitation
        self._user = user
        self._team = team
        self._role = role

    @property
    def team_member_id(self):
        return self._team_member_id

    @property
    def external_id(self):
        return self._external_id

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
    def is_added_by_group(self):
        return self._is_added_by_group

    @property
    def hide_passwords(self):
        return self._hide_passwords

    @hide_passwords.setter
    def hide_passwords(self, hide_passwords_value):
        self._hide_passwords = hide_passwords_value

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key_value):
        self._key = key_value

    @property
    def reset_password_key(self):
        return self._reset_password_key

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status_value):
        self._status = status_value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email_value):
        self._email = email_value

    @property
    def token_invitation(self):
        return self._token_invitation

    @property
    def user(self):
        return self._user

    @property
    def team(self):
        return self._team

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role_value):
        self._role = role_value
