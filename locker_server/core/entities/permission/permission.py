class Permission(object):
    def __init__(self, permission_id: int, scope: str = None, codename: str = None, description: str = ""):
        self._permission_id = permission_id
        self._scope = scope
        self._codename = codename
        self._description = description

    @property
    def permission_id(self):
        return self._permission_id

    @property
    def scope(self):
        return self._scope

    @property
    def codename(self):
        return self._codename

    @property
    def description(self):
        return self._description
