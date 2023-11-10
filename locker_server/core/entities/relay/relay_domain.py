class RelayDomain(object):
    def __init__(self, relay_domain_id: str):
        self._relay_domain_id = relay_domain_id

    @property
    def relay_domain_id(self):
        return self._relay_domain_id
