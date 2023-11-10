

class Country(object):
    def __init__(self, country_code: str, country_name: str, country_phone_code: str):
        self._country_code = country_code
        self._country_name = country_name
        self._country_phone_code = country_phone_code

    @property
    def country_code(self):
        return self._country_code

    @property
    def country_name(self):
        return self._country_name

    @property
    def country_phone_code(self):
        return self._country_phone_code
