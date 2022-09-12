import json
import os
import requests
from requests import Response
import time

from django.conf import settings
# from rest_framework.response import Response

from shared.error_responses.error import refer_error, gen_error


def requester(method, url, headers=None, data_send=None, retry=False, max_retries=10, timeout=10):
    if data_send is None:
        data_send = dict()
    if headers is None:
        headers = {}

    env = os.getenv("PROD_ENV", "dev")
    if env == "staging":
        headers.update({
            "CF-Access-Client-Id": settings.CF_ACCESS_CLIENT_ID,
            "CF-Access-Client-Secret": settings.CF_ACCESS_CLIENT_SECRET
        })

    if isinstance(data_send, dict) is False and isinstance(data_send, list) is False:
        # Invalid Json data
        res = Response()
        res.status_code = 400
        res._content = json.dumps(refer_error(gen_error("0004"))).encode('utf-8')
        return res

    number_retries = 0
    while True:
        try:
            res = None
            if method.lower() == "get":
                res = requests.get(headers=headers, url=url, verify=False, timeout=timeout)
            elif method.lower() == "post":
                res = requests.post(headers=headers, url=url, json=data_send, verify=False, timeout=timeout)
            elif method.lower() == "put":
                res = requests.put(headers=headers, url=url, json=data_send, verify=False, timeout=timeout)
            elif method.lower() == "delete":
                res = requests.delete(headers=headers, url=url, json=data_send, verify=False, timeout=timeout)
            if res is None:
                res = Response()
                res.status_code = 400
                res._content = json.dumps(refer_error(gen_error("0008"))).encode('utf-8')
                return res
            return res
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            number_retries += 1
            if retry:
                if number_retries <= max_retries:
                    time.sleep(3)
                    continue
                else:
                    res = Response()
                    res.status_code = 400
                    res._content = json.dumps(refer_error(gen_error("0009"))).encode('utf-8')
                    return res
            else:
                res = Response()
                res.status_code = 400
                res._content = json.dumps(refer_error(gen_error("0009"))).encode('utf-8')
                return res


class RequesterError(requests.ConnectionError):
    pass
