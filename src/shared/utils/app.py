import hashlib
import random
import string
import time
import urllib.parse
import pytz
from datetime import datetime, timezone
from dateutil import relativedelta

from shared.constants.ciphers import *


def now(return_float=False):
    """
    Get time now (Unix time)
    :param return_float: (bool) Return float
    :return: timestamp
    """
    if return_float:
        return time.time()
    time_now = datetime.now(tz=pytz.UTC)
    timestamp_now = time_now.timestamp()
    return int(timestamp_now)


def datetime_from_ts(ts):
    try:
        ts = int(ts)
        return datetime.fromtimestamp(ts, tz=pytz.UTC)
    except (AttributeError, TypeError, ValueError):
        return None


def random_n_digit(n):
    """
    Generating new random string
    :param n: Number characters
    :return: random string contains number and ascii lower
    """
    return ''.join([random.choice(string.digits + string.ascii_lowercase) for _ in range(n)])


def sha_256_encryption(text):
    """
    Encrypting string by sha-256
    :param text:
    :return:
    """
    sha_signature = hashlib.sha256(text.encode()).hexdigest()
    return sha_signature


def diff_list(new_list, old_list):
    """
    Get diff from 2 list
    :param new_list:
    :param old_list:
    :return:
    """
    return [x for x in new_list if x not in old_list]


def url_decode(url):
    """
    Decode url utf-8
    :param url:
    :return:
    """
    url = url.replace("+", "%20")
    url = urllib.parse.unquote(url)
    return url


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
