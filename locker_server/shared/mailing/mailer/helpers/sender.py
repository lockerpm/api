class Sender:
    def __init__(self, raw):
        self._raw = raw

    @property
    def name(self):
        return self._raw['sender_name']

    @property
    def address(self):
        return self._raw['sender_email']

    @property
    def reply_name(self):
        try:
            return self._raw['reply_to']['name']
        except (KeyError, TypeError):
            return None

    @property
    def reply_address(self):
        try:
            return self._raw['reply_to']['email']
        except (KeyError, TypeError):
            return None

    def to_string(self):
        return self._raw
