import json
from datetime import datetime
from typing import Dict
from bs4 import BeautifulSoup
import requests

from cystack_models.factory.user_reward_mission.mission import Mission, MAX_REVIEW_DURATION_TIME
from shared.constants.device_type import *
from shared.log.cylog import CyLog
from shared.utils.app import now


class ExtensionInstallationAndReviewMission(Mission):

    def check_mission_completion(self, input_data: Dict):
        user = input_data.get("user")
        user_identifier = input_data.get("user_identifier")
        extension_devices = list(user.user_devices.filter(
            client_id=CLIENT_ID_BROWSER
        ).values_list('device_type', flat=True).distinct())
        if len(extension_devices) < 2:
            return False
        map_extension_type_check = {
            DEVICE_TYPE_EXTENSION_CHROME: self.check_chrome_extension,
            DEVICE_TYPE_EXTENSION_FIREFOX: self.check_firefox_extension,
            DEVICE_TYPE_EXTENSION_EDGE: self.check_edge_extension,
            DEVICE_TYPE_EXTENSION_SAFARI: self.check_safari_extension,
            DEVICE_TYPE_EXTENSION_BRAVE: self.check_brave_extension,
            DEVICE_TYPE_EXTENSION_OPERA: self.check_opera_extension,
        }
        review_count = 0
        for extension_device in extension_devices:
            if map_extension_type_check.get(extension_device)(user_identifier) is True:
                review_count +=1
        return True if review_count >= 2 else False

    @staticmethod
    def check_chrome_extension(user_identifier):
        url = "https://chrome.google.com/webstore/reviews/get?hl=en&gl=VN&pv=20210820"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data_send = {
            "f.req": '["http://chrome.google.com/extensions/permalink?'
                     'id=cmajindocfndlkpkjnmjpjoilibjgmgh",null,[25,0],2,[2]]'
        }
        res = requests.post(url=url, data=data_send, headers=headers)
        if res.status_code != 200:
            return False
        data = res.text.replace(")]}'\n", "", 1)
        try:
            data = json.loads(data)
        except:
            CyLog.warning(**{"message": f"[!] check_chrome_extension json error: {data}"})
            return False
        item_reviews = data[1][4]
        for item_review in item_reviews:
            try:
                review_time = item_review[6]
                review_name = item_review[2][1]
                review_text = item_review[4]
                review_star = item_review[3]
            except IndexError:
                continue
            # The review time must be in 24 hours
            if (review_time / 1000) < now() - MAX_REVIEW_DURATION_TIME:
                continue
            if review_name == user_identifier and review_star >= 4:
                return True
        return False

    @staticmethod
    def check_firefox_extension(user_identifier):
        # TODO: Change the extension addon id
        addon_id = ""
        url = f"https://addons.mozilla.org/api/v5/ratings/rating/?addon={addon_id}&lang=en-US&score=4,5&page_size=50"
        max_page = 2
        page = 1
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
        }
        reviews = []
        while page <= max_page:
            url += f"&page={page}"
            res = requests.get(url=url, headers=headers)
            if res.status_code != 200:
                break
            reviews += res.json().get("results")
            page += 1
        for review in reviews:
            try:
                created_time = datetime.strptime(review.get("created"), "%Y-%m-%dT%H:%M:%SZ").timestamp()
            except TypeError:
                continue
            if created_time < now() - MAX_REVIEW_DURATION_TIME:
                continue
            if review.get("user").get("name") == user_identifier:
                return True
        return False

    @staticmethod
    def check_edge_extension(user_identifier):
        # TODO: Change the extension addon id
        addon_id = ""
        page_size = 25
        skip_item = 0
        max_size = 50
        continue_token = ""
        url = f"https://ratingsedge.rnr.microsoft.com/v1.0/ratingsedge/product/{addon_id}?" \
              f"catalogId=1&pageSize={page_size}&orderBy=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.58"
        }
        reviews = []
        while skip_item < max_size:
            url += f"&skipItems={skip_item}"
            if continue_token:
                url += f"&continuationToken={continue_token}"
            res = requests.get(url=url, headers=headers)
            if res.status_code != 200:
                break
            reviews += res.json().get("Items", [])
            skip_item += page_size
            continue_token = res.json().get("PagingInfo").get("ContinuationToken", "")
        for review in reviews:
            if review.get("Rating") not in [4, 5]:
                continue
            try:
                created_time = datetime.strptime(review.get("SubmittedDateTime"), "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            except TypeError:
                continue
            if created_time < now() - MAX_REVIEW_DURATION_TIME:
                continue
            if review.get("UserName") == user_identifier:
                return True
        return False

    @staticmethod
    def check_safari_extension(user_identifier):
        url = ""
        return False

    def check_brave_extension(self, user_identifier):
        return self.check_chrome_extension(user_identifier)

    @staticmethod
    def check_opera_extension(user_identifier):
        # TODO: Change the extension addon id
        addon_id = ""
        url = f"https://forums.opera.com/comments/get/addons/{addon_id}/en"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.58",
            "Authority": "forums.opera.com",
            "Origin": "https://addons.opera.com"
        }
        res = requests.get(url=url, headers=headers)
        if res.status_code != 200:
            return False
        content = res.json().get("content")
        soup = BeautifulSoup(content, features="html.parser")
        review_elements = soup.find_all("small", {"class": "post-header"})
        for review_element in review_elements:
            name = review_element.a.strong.text
            try:
                review_time_str = review_element.contents[2].get("title")
                review_time = datetime.strptime(review_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            except (IndexError, TypeError):
                continue
            if review_time < now() - MAX_REVIEW_DURATION_TIME:
                continue
            if name == user_identifier:
                return True
        return False
