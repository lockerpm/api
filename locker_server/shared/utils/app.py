import random
import string
import time
from datetime import datetime, timezone

import pytz
from dateutil import relativedelta
from typing import List
from user_agents import parse
import json
import humps

from locker_server.shared.constants.ciphers import *


def datetime_from_ts(ts):
    try:
        ts = int(ts)
        return datetime.fromtimestamp(ts, tz=pytz.UTC)
    except (AttributeError, TypeError, ValueError):
        return None


def now(return_float=False):
    """
    Get time now (UNIX timestamp)
    :return: timestamp
    """
    time_now = time.time()
    return time_now if return_float else int(time_now)


def diff_list(in_list: List, not_in_list: List) -> List:
    """
    This function gets all elements in `in_list` without not in `not_in_list`
    :param in_list: (list)
    :param not_in_list: (list)
    :return:
    """
    return [x for x in in_list if x not in not_in_list]


def random_n_digit(n: int, allow_uppercase: bool = False) -> str:
    """
    Generating new random string
    :param n: (int) Number characters
    :param allow_uppercase: (bool) Allow upper case
    :return: A random string contains number and ascii lower
    """
    valid_digits = string.digits + string.ascii_lowercase
    if allow_uppercase is True:
        valid_digits += string.ascii_uppercase
    return ''.join([random.choice(valid_digits) for _ in range(n)])


def get_ip_location(ip):
    """
    This function to get {location, ip} from the request
    :param ip: The IP address
    :return: (dict) {location, ip}
    """
    from django.contrib.gis.geoip2 import GeoIP2
    location = dict()
    try:
        g = GeoIP2()
        location = g.city(ip) or {}
        city = location.get("city", "")
        country = location.get("country_name", "")
        city_country = []
        if city is not None and city != "":
            city_country.append(city)
        if country is not None and country != "":
            city_country.append(country)
        city_country_str = ", ".join(city_country)
        location.update({"city_country": city_country_str})
    except Exception as e:
        location.update({"city_country": ''})
    return {
        "location": location,
        "ip": ip
    }


# def get_otp_uri(otp_secret: str, username: str = None):
#     totp = pyotp.TOTP(otp_secret)
#     uri = totp.provisioning_uri(name=username, issuer_name="Secrets")
#     return uri


def get_factor2_expired_date(method: str) -> float:
    """
    Return expired time from current time by otp method
    :param method: (str) OTP method
    :return:
    """
    return 0


def get_user_agent(request):
    """
    Return user agent info from request
    """
    user_agent_str = request.META['HTTP_USER_AGENT']
    if not isinstance(user_agent_str, str):
        user_agent_str = user_agent_str.decode('utf-8')
    user_agent = parse(user_agent_string=user_agent_str)
    return user_agent


def secure_random_string(length: int, alpha: bool = True, upper: bool = True, lower: bool = True,
                         numeric: bool = True, special: bool = False):
    return secure_random_string_generator(
        length=length,
        characters=random_string_characters(alpha, upper, lower, numeric, special)
    )


def secure_random_string_generator(length: int, characters: str):
    if length < 0:
        raise Exception("Length cannot be less than zero")
    if not characters:
        raise Exception("Character is not valid")
    random_str = "".join([random.choice(characters) for _ in range(length)])
    return random_str


def random_string_characters(alpha: bool, upper: bool, lower: bool, numeric: bool, special: bool):
    characters = ""
    if alpha:
        if upper:
            characters += string.ascii_uppercase
        if lower:
            characters += string.ascii_lowercase
    if numeric:
        characters += string.digits
    if special:
        characters += "!@#$%^*&"
    return characters


def start_end_month_current():
    current_time = datetime.now(timezone.utc)
    start_ts = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()
    end_ts = (current_time + relativedelta.relativedelta(months=1)).timestamp()
    return start_ts, end_ts


def get_cipher_detail_data(cipher):
    cipher_type = cipher.get("type")
    if cipher_type == CIPHER_TYPE_LOGIN:
        data = dict(cipher.get("login") or {})
    elif cipher_type == CIPHER_TYPE_CARD:
        data = dict(cipher.get("card") or {})
    elif cipher_type == CIPHER_TYPE_IDENTITY:
        data = dict(cipher.get("identity") or {})
    elif cipher_type == CIPHER_TYPE_NOTE:
        data = dict(cipher.get("secureNote") or {})
    elif cipher_type == CIPHER_TYPE_TOTP:
        data = dict(cipher.get("secureNote") or {})
    elif cipher_type == CIPHER_TYPE_CRYPTO_ACCOUNT:
        data = dict(cipher.get("cryptoAccount") or {})
    elif cipher_type == CIPHER_TYPE_CRYPTO_WALLET:
        data = dict(cipher.get("cryptoWallet") or {})
    elif cipher_type == CIPHER_TYPE_MASTER_PASSWORD:
        data = dict(cipher.get("login") or {})
    elif cipher_type in [CIPHER_TYPE_DRIVER_LICENSE, CIPHER_TYPE_CITIZEN_ID, CIPHER_TYPE_PASSPORT,
                         CIPHER_TYPE_SOCIAL_SECURITY_NUMBER, CIPHER_TYPE_WIRELESS_ROUTER, CIPHER_TYPE_SERVER,
                         CIPHER_TYPE_API, CIPHER_TYPE_DATABASE]:
        data = dict(cipher.get("secureNote") or {})
    else:
        data = dict()
    data.update({
        "name": cipher.get("name"),
        "fields": cipher.get("fields")
    })
    if cipher.get("notes"):
        data.update({"notes": cipher.get("notes")})
    return data


def camel_snake_data(json_data, camel_to_snake=False, snake_to_camel=False):
    """
    Get JSON response data from HTTPResponse
    :param json_data: (dict) The data is needed to convert
    :param camel_to_snake: (bool) Convert from camel case to snake case
    :param snake_to_camel: (bool) Convert from snake case to camel case
    :return: (dict)
    """
    try:
        if camel_to_snake is True:
            return humps.decamelize(json_data)
        if snake_to_camel is True:
            return humps.camelize(json_data)
        return json_data
    except json.decoder.JSONDecodeError:
        return json_data


def convert_readable_date(timestamp, datetime_format="%Y-%m-%dT%H:%M:%S.%fZ"):
    """
    Convert timestamp to readable date string
    :param timestamp: (int)
    :param datetime_format
    :return:
    """
    if timestamp is None or timestamp < 0:
        return None
    return datetime.utcfromtimestamp(timestamp).strftime(datetime_format)
