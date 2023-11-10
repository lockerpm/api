from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.policy.policy import EnterprisePolicy


class PolicyFailedLogin(EnterprisePolicy):
    def __init__(self, policy_id: int, enterprise: Enterprise, policy_type: str, enabled: bool = False,
                 failed_login_attempts: int = None, failed_login_duration: int = 600,
                 failed_login_block_time: int = 900, failed_login_owner_email: bool = False):
        super().__init__(policy_id=policy_id, enterprise=enterprise, policy_type=policy_type, enabled=enabled)
        self._failed_login_attempts = failed_login_attempts
        self._failed_login_duration = failed_login_duration
        self._failed_login_block_time = failed_login_block_time
        self._failed_login_owner_email = failed_login_owner_email

    @property
    def failed_login_attempts(self):
        return self._failed_login_attempts

    @property
    def failed_login_duration(self):
        return self._failed_login_duration

    @property
    def failed_login_block_time(self):
        return self._failed_login_block_time

    @property
    def failed_login_owner_email(self):
        return self._failed_login_owner_email

    def get_config_json(self):
        return {
            "failed_login_attempts": self.failed_login_attempts,
            "failed_login_duration": self.failed_login_duration,
            "failed_login_block_time": self.failed_login_block_time,
            "failed_login_owner_email": self.failed_login_owner_email,
        }
