import hashlib
import urllib.parse

from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError


# Get gravatar by email
def get_avatar(email):
    size = 128
    gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower().encode("utf-8")).hexdigest() + "?"
    gravatar_url += urllib.parse.urlencode({'d': "identicon", 's': str(size)})

    return gravatar_url


def check_email(text):
    """
    Check text is email format
    :param text: String need check
    :return: True / False
    """
    try:
        email_validator = EmailValidator()
        email_validator(text)
        user_part, domain_part = text.rsplit('@', 1)
        if len(user_part) > 64:
            return False
        return True
    except ValidationError as e:
        return False
