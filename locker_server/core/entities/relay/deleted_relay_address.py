class DeletedRelayAddress(object):
    def __init__(self, deleted_relay_address_id: int, address_hash: str = None, num_forwarded: int = 0,
                 num_blocked: int = 0, num_replied: int = 0, num_spam: int = 0):
        self._deleted_relay_address_id = deleted_relay_address_id
        self._address_hash = address_hash
        self._num_forwarded = num_forwarded
        self._num_blocked = num_blocked
        self._num_replied = num_replied
        self._num_spam = num_spam

    @property
    def deleted_relay_address_id(self):
        return self._deleted_relay_address_id

    @property
    def address_hash(self):
        return self._address_hash

    @property
    def num_forwarded(self):
        return self._num_forwarded

    @property
    def num_blocked(self):
        return self._num_blocked

    @property
    def num_replied(self):
        return self._num_replied

    @property
    def num_spam(self):
        return self._num_spam
