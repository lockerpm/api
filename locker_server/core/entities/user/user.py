from locker_server.shared.constants.account import DEFAULT_KDF_ITERATIONS, LOGIN_METHOD_PASSWORD, \
    DEFAULT_ONBOARDING_PROCESS
from locker_server.shared.constants.lang import LANG_ENGLISH
from locker_server.shared.utils.avatar import get_avatar


class User(object):
    def __init__(self, user_id: int, internal_id: str = None, creation_date: float = None, revision_date: float = None,
                 first_login: float = None, activated: bool = False, activated_date: float = None,
                 delete_account_date: float = None, account_revision_date: float = None,
                 master_password: str = None, master_password_hint: str = "",
                 master_password_score: int = 0, security_stamp: str = None, key: str = None,
                 public_key: str = None, private_key: str = None, kdf: int = 0, kdf_iterations=DEFAULT_KDF_ITERATIONS,
                 api_key: str = None, timeout: int = 20160, timeout_action: str = "lock", is_leaked: bool = False,
                 use_relay_subdomain: bool = False, last_request_login: float = None, login_failed_attempts: int = 0,
                 login_block_until: float = None, login_method: str = LOGIN_METHOD_PASSWORD,
                 fd_credential_id: str = None, fd_random: str = None,
                 onboarding_process: str = DEFAULT_ONBOARDING_PROCESS, saas_source: str = None,
                 email: str = None, full_name: str = None, language: str = LANG_ENGLISH,
                 is_factor2: bool = False, base32_secret_factor2: str = "", is_super_admin: bool = False,
                 sync_all_platforms: bool = False, is_password_changed: bool = True):
        self._user_id = user_id
        self._internal_id = internal_id
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._first_login = first_login
        self._activated = activated
        self._activated_date = activated_date
        self._deleted_account_date = delete_account_date
        self._account_revision_date = account_revision_date
        self._master_password = master_password
        self._master_password_hint = master_password_hint
        self._master_password_score = master_password_score
        self._security_stamp = security_stamp
        self._key = key
        self._public_key = public_key
        self._private_key = private_key
        self._kdf = kdf
        self._kdf_iterations = kdf_iterations
        self._api_key = api_key
        self._timeout = timeout
        self._timeout_action = timeout_action
        self._is_leaked = is_leaked
        self._use_relay_subdomain = use_relay_subdomain
        self._last_request_login = last_request_login
        self._login_failed_attempts = login_failed_attempts
        self._login_block_until = login_block_until
        self._login_method = login_method
        self._fd_credential_id = fd_credential_id
        self._fd_random = fd_random
        self._onboarding_process = onboarding_process
        self._saas_source = saas_source
        self._email = email
        self._full_name = full_name
        self._language = language
        self._is_factor2 = is_factor2
        self._base32_secret_factor2 = base32_secret_factor2
        self._is_super_admin = is_super_admin
        self._sync_all_platforms = sync_all_platforms
        self._is_password_changed = is_password_changed

    def __str__(self):
        return f"<User object {self._user_id}>"

    @property
    def user_id(self):
        return self._user_id

    @property
    def internal_id(self):
        return self._internal_id

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date

    @property
    def first_login(self):
        return self._first_login

    @property
    def activated(self):
        return self._activated

    @property
    def activated_date(self):
        return self._activated_date

    @property
    def delete_account_date(self):
        return self._deleted_account_date

    @property
    def account_revision_date(self):
        return self._account_revision_date

    @property
    def master_password(self):
        return self._master_password

    @property
    def master_password_hint(self):
        return self._master_password_hint

    @property
    def master_password_score(self):
        return self._master_password_score

    @property
    def security_stamp(self):
        return self._security_stamp

    @property
    def key(self):
        return self._key

    @property
    def public_key(self):
        return self._public_key

    @property
    def private_key(self):
        return self._private_key

    @property
    def kdf(self):
        return self._kdf

    @property
    def kdf_iterations(self):
        return self._kdf_iterations

    @property
    def api_key(self):
        return self._api_key

    @property
    def timeout(self):
        return self._timeout

    @property
    def timeout_action(self):
        return self._timeout_action

    @property
    def is_leaked(self):
        return self._is_leaked

    @property
    def use_relay_subdomain(self):
        return self._use_relay_subdomain

    @property
    def last_request_login(self):
        return self._last_request_login

    @property
    def login_failed_attempts(self):
        return self._login_failed_attempts

    @property
    def login_block_until(self):
        return self._login_block_until

    @property
    def login_method(self):
        return self._login_method

    @property
    def fd_credential_id(self):
        return self._fd_credential_id

    @property
    def fd_random(self):
        return self._fd_random

    @property
    def onboarding_process(self):
        return self._onboarding_process

    @property
    def saas_source(self):
        return self._saas_source

    @property
    def email(self):
        return self._email

    @property
    def username(self):
        return self._email

    @property
    def full_name(self):
        return self._full_name

    @property
    def language(self):
        return self._language

    @property
    def is_factor2(self):
        return self._is_factor2

    @property
    def base32_secret_factor2(self):
        return self._base32_secret_factor2

    @property
    def is_super_admin(self):
        return self._is_super_admin

    @property
    def sync_all_platforms(self):
        return self._sync_all_platforms

    @property
    def is_password_changed(self):
        return self._is_password_changed

    def get_avatar(self):
        return get_avatar(self.email)
