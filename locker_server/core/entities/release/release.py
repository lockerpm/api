import ast


class Release(object):
    def __init__(self, release_id: int, created_time: int = None, major: str = None, minor: str = None,
                 patch: str = None, build_number: str = None, description_en: str = "", description_vi: str = "",
                 client_id: str = None, environment: str = "prod", checksum: str = None):
        self._release_id = release_id
        self._created_time = created_time
        self._major = major
        self._minor = minor
        self._patch = patch
        self._build_number = build_number
        self._description_en = description_en
        self._description_vi = description_vi
        self._client_id = client_id
        self._environment = environment
        self._checksum = checksum

    @property
    def release_id(self):
        return self._release_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def major(self):
        return self._major

    @property
    def minor(self):
        return self._minor

    @property
    def patch(self):
        return self._patch

    @property
    def build_number(self):
        return self._build_number

    @property
    def description_en(self):
        return self._description_en

    @property
    def description_vi(self):
        return self._description_vi

    @property
    def client_id(self):
        return self._client_id

    @property
    def environment(self):
        return self._environment

    @property
    def version(self):
        ver = f"{self._major}.{self._minor}"
        if self._patch:
            ver += f".{self._patch}"
        if self._build_number:
            ver += f".{self._build_number}"

        return ver

    @property
    def checksum(self):
        return self._checksum

    def get_checksum(self):
        if not self.checksum:
            return {}
        return ast.literal_eval(str(self.checksum))
