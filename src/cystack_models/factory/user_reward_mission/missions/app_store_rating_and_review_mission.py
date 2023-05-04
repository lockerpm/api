import ast
import jwt
import requests
from datetime import datetime
from typing import Dict

from cystack_models.factory.user_reward_mission.mission import Mission, MAX_REVIEW_DURATION_TIME
from shared.external_request.requester import requester
from shared.log.cylog import CyLog
from shared.utils.app import now


class AppStoreRatingAndReviewMission(Mission):

    def check_mission_completion(self, input_data: Dict):
        user_identifier = input_data.get("user_identifier")
        app_id = "1586927301"
        url = f"https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews"
        headers = {
            "Authorization": f"Bearer {self._generate_jwt_token(app_id=app_id)}"
        }
        try:
            res = requester(method="GET", url=url, headers=headers, timeout=10)
            if res.status_code != 200:
                CyLog.warning(**{"message": "[!] AppStoreRatingAndReviewMission.check_mission_completion request error:"
                                            " {} {}".format(res.status_code, res.text)})
                return False
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout):
            return False

        reviews = res.json().get("data", [])
        for review in reviews:
            try:
                created_time = datetime.fromisoformat(review.get("attributes", {}).get("createdDate")).timestamp()
            except TypeError:
                continue
            if created_time < now() - MAX_REVIEW_DURATION_TIME:
                continue
            if review.get("attributes", {}).get("reviewerNickname") == user_identifier:
                return True
        return False

    @staticmethod
    def _generate_jwt_token(app_id: str, key_pair=None):
        if not key_pair:
            from django.conf import settings
            key_pair = ast.literal_eval(str(settings.APPSTORE_KEY_PAIR))
        headers = {
            "alg": "ES256",
            "kid": key_pair.get("key_id"),
            "typ": "JWT"
        }
        payload = {
            "iss": key_pair.get("iss_id"),
            "iat": now(),
            "exp": now() + 10 * 60,
            "aud": "appstoreconnect-v1",
            "scope": [
                f"GET /v1/apps/{app_id}/customerReviews"
            ]
        }
        token = jwt.encode(payload=payload, key=key_pair.get("secret"), headers=headers)
        return token
