class SaasMarket(object):
    def __init__(self, saas_market_id: int, name: str, lifetime_duration: int = None):
        self._saas_market_id = saas_market_id
        self._name = name
        self._lifetime_duration = lifetime_duration

    @property
    def saas_market_id(self):
        return self._saas_market_id

    @property
    def name(self):
        return self._name

    @property
    def lifetime_duration(self):
        return self._lifetime_duration
