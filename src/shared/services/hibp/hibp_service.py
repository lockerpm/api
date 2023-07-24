import re
import time

import requests
import urllib.parse

from django.conf import settings

from shared.log.cylog import CyLog

HIBP_API = "https://haveibeenpwned.com/api/v3/breachedaccount/{}?truncateResponse=false&includeUnverified=false"
HEADERS = {
    # 'User-agent': 'CyStack Locker',
    "hibp-api-key": settings.HIBP_API_KEY
}


class HibpService:
    def __init__(self, retries_number=3):
        self.retries_number = retries_number

    def check_breach(self, email):
        email = urllib.parse.quote_plus(email)
        url = HIBP_API.format(email)

        retry = 0
        while True:
            res = requests.get(url=url, headers=HEADERS)
            CyLog.info(**{
                "message": f"[hibp] Check result {email} - {res.status_code} - {res.text}",
                "output": ["stdout"]
            })
            if 200 <= res.status_code < 300:
                return res.json()
            elif res.status_code == 404:
                return {}
            elif res.status_code == 429:
                try:
                    timeout = int(re.findall(r'\d+', res.json().get("message"))[0])
                    timeout = min(timeout, 10)
                except (AttributeError, KeyError, IndexError, ValueError):
                    timeout = 3
                time.sleep(timeout)
            retry += 1
            if retry >= self.retries_number:
                break
        CyLog.error(**{"message": "[hibp] All retries number of checking breach reached: {}".format(url)})
        return {}
