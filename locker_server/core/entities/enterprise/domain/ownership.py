class Ownership(object):
    def __init__(self, ownership_id: str, description: str = ""):
        self._ownership_id = ownership_id
        self._description = description

    @property
    def ownership_id(self):
        return self._ownership_id

    @property
    def description(self):
        return self._description
