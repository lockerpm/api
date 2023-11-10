class Reply(object):
    def __init__(self, reply_id: int, lookup: str, encrypted_metadata: str = None, created_at: float = None):
        self._reply_id = reply_id
        self._lookup = lookup
        self._encrypted_metadata = encrypted_metadata
        self._created_at = created_at

    @property
    def reply_id(self):
        return self._reply_id

    @property
    def lookup(self):
        return self._lookup

    @property
    def encrypted_metadata(self):
        return self._encrypted_metadata

    @property
    def created_at(self):
        return self._created_at
