from locker_server.core.entities.payment.country import Country


class Customer(object):
    def __init__(self, customer_id: int, full_name: str = None, organization: str = None, address: str = None,
                 city: str = None, state: str = None, postal_code: str = None, phone_number: str = None,
                 last4: str = None, brand: str = None, country: Country = None):
        self._customer_id = customer_id
        self._full_name = full_name
        self._organization = organization
        self._address = address
        self._city = city
        self._state = state
        self._postal_code = postal_code
        self._phone_number = phone_number
        self._last4 = last4
        self._brand = brand
        self._country = country

    @property
    def customer_id(self):
        return self._customer_id

    @property
    def full_name(self):
        return self._full_name

    @property
    def organization(self):
        return self._organization

    @property
    def address(self):
        return self._address

    @property
    def city(self):
        return self._city

    @property
    def state(self):
        return self._state

    @property
    def postal_code(self):
        return self._postal_code

    @property
    def phone_number(self):
        return self._phone_number

    @property
    def last4(self):
        return self._last4

    @property
    def brand(self):
        return self._brand

    @property
    def country(self):
        return self._country
