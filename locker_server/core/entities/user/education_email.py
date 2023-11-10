from locker_server.core.entities.user.user import User


class EducationEmail(object):
    def __init__(self, education_email_id: int, created_time: float, email: str,
                 education_type: str = "student", university: str = "", verified: bool = False,
                 verification_token: str = None, promo_code: str = None, user: User = None):
        self._education_email_id = education_email_id
        self._created_time = created_time
        self._email = email
        self._education_type = education_type
        self._university = university
        self._verified = verified
        self._verification_token = verification_token
        self._promo_code = promo_code
        self._user = user

    @property
    def education_email_id(self):
        return self._education_email_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def email(self):
        return self._email

    @property
    def education_type(self):
        return self._education_type

    @property
    def university(self):
        return self._university

    @property
    def verified(self):
        return self._verified

    @property
    def verification_token(self):
        return self._verification_token

    @property
    def promo_code(self):
        return self._promo_code

    @property
    def user(self):
        return self._user

