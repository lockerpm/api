from locker_server.core.entities.enterprise.enterprise import Enterprise


class EnterpriseBillingContact(object):
    def __init__(self, enterprise_billing_contact_id: int, created_time: float = None, email: str = None,
                 enterprise: Enterprise = None):
        self._enterprise_billing_contact_id = enterprise_billing_contact_id
        self._created_time = created_time
        self._email = email
        self._enterprise = enterprise

    @property
    def enterprise_billing_contact_id(self):
        return self._enterprise_billing_contact_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def email(self):
        return self._email

    @property
    def enterprise(self):
        return self._enterprise
