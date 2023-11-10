from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.policy.policy import EnterprisePolicy


class PolicyPasswordless(EnterprisePolicy):
    def __init__(self, policy_id: int, enterprise: Enterprise, policy_type: str, enabled: bool = False,
                 only_allow_passwordless: bool = False):
        super().__init__(policy_id=policy_id, enterprise=enterprise, policy_type=policy_type, enabled=enabled)
        self._only_allow_passwordless = only_allow_passwordless

    @property
    def only_allow_passwordless(self):
        return self._only_allow_passwordless

    def get_config_json(self):
        return {
            "only_allow_passwordless": self.only_allow_passwordless,
        }
