from locker_server.core.entities.enterprise.enterprise import Enterprise


class EnterprisePolicy(object):
    def __init__(self, policy_id: int, enterprise: Enterprise, policy_type: str, enabled: bool = False):
        self._policy_id = policy_id
        self._enterprise = enterprise
        self._policy_type = policy_type
        self._enabled = enabled
        self._config = None

    @property
    def policy_id(self):
        return self._policy_id

    @property
    def enterprise(self):
        return self._enterprise

    @property
    def policy_type(self):
        return self._policy_type

    @property
    def enabled(self):
        return self._enabled

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config_value):
        self._config = config_value

    def get_config_json(self):
        if not self.config:
            return {}
        return self.config.get_config_json()
