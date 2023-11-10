

class PromoCodeType(object):
    def __init__(self, name: str, description: str = ""):
        self._name = name
        self._description = description

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description
