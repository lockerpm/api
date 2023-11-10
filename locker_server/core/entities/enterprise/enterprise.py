from locker_server.shared.utils.avatar import get_avatar


class Enterprise(object):
    def __init__(self, enterprise_id: str, name: str, description: str = '', creation_date: float = None,
                 revision_date: float = None, locked: bool = False, enterprise_name: str = "",
                 enterprise_address1: str = "", enterprise_address2: str = "", enterprise_phone: str = "",
                 enterprise_country: str = None, enterprise_postal_code: str = "", init_seats: int = None,
                 init_seats_expired_time: float = None, avatar: str = None):
        self._enterprise_id = enterprise_id
        self._name = name
        self._description = description
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._locked = locked
        self._enterprise_name = enterprise_name
        self._enterprise_address1 = enterprise_address1
        self._enterprise_address2 = enterprise_address2
        self._enterprise_phone = enterprise_phone
        self._enterprise_country = enterprise_country
        self._enterprise_postal_code = enterprise_postal_code
        self._init_seats = init_seats
        self._init_seats_expired_time = init_seats_expired_time
        self._avatar = avatar

    @property
    def enterprise_id(self):
        return self._enterprise_id

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date

    @property
    def locked(self):
        return self._locked

    @property
    def enterprise_name(self):
        return self._enterprise_name

    @property
    def enterprise_address1(self):
        return self._enterprise_address1

    @property
    def enterprise_address2(self):
        return self._enterprise_address2

    @property
    def enterprise_phone(self):
        return self._enterprise_phone

    @property
    def enterprise_country(self):
        return self._enterprise_country

    @property
    def enterprise_postal_code(self):
        return self._enterprise_postal_code

    @property
    def init_seats(self):
        return self._init_seats

    @property
    def init_seats_expired_time(self):
        return self._init_seats_expired_time

    @property
    def avatar(self):
        return self._avatar or get_avatar(email=self.enterprise_id)
