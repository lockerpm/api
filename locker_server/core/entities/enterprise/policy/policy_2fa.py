import json

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.policy.policy import EnterprisePolicy


class Policy2FA(EnterprisePolicy):
    def __init__(self, policy_id: int, enterprise: Enterprise, policy_type: str, enabled: bool = False,
                 only_admin: bool = True):
        super().__init__(policy_id=policy_id, enterprise=enterprise, policy_type=policy_type, enabled=enabled)
        self._only_admin = only_admin

    @property
    def only_admin(self):
        return self._only_admin

    def get_config_json(self):
        return {
            "only_admin": self.only_admin
        }
