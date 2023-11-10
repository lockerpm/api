class AffiliateSubmission(object):
    def __init__(self, affiliate_submission_id: int, created_time: float = None, full_name: str = None,
                 email: str = None, phone: str = None, company: str = None, country: str = None,
                 status: str = "submitted"):
        self._affiliate_submission_id = affiliate_submission_id
        self._created_time = created_time
        self._full_name = full_name
        self._email = email
        self._phone = phone
        self._company = company
        self._country = country
        self._status = status

    @property
    def affiliate_submission_id(self):
        return self._affiliate_submission_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def full_name(self):
        return self._full_name

    @property
    def email(self):
        return self._email

    @property
    def phone(self):
        return self._phone

    @property
    def company(self):
        return self._company

    @property
    def country(self):
        return self._country

    @property
    def status(self):
        return self._status
