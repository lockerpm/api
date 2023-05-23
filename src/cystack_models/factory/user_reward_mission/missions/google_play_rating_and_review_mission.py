import ast
from typing import Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from django.conf import settings

from cystack_models.factory.user_reward_mission.mission import Mission, MAX_REVIEW_DURATION_TIME
from shared.constants.missions import REWARD_TYPE_PROMO_CODE
from shared.utils.app import now


class GooglePlayRatingAndReviewMission(Mission):

    def __init__(self, mission_type: str, extra_requirements=None):
        super().__init__(mission_type, extra_requirements)
        self.reward_type = REWARD_TYPE_PROMO_CODE
        self.reward_value = 5
        google_play_credentials = Credentials.from_service_account_info(
            ast.literal_eval(str(settings.GOOGLE_PLAY_SERVICE_ACCOUNT)),
            scopes=['https://www.googleapis.com/auth/androidpublisher']
        )
        self.google_play_service = build("androidpublisher", "v3", credentials=google_play_credentials)

    def check_mission_completion(self, input_data: Dict):
        user_identifier = input_data.get("user_identifier")

        # This function only returns reviews from last week
        reviews = self.google_play_service.reviews().list(
            packageName="com.cystack.locker",
            translationLanguage=None,
            # token=None,
            maxResults=100,
            # startIndex=None
        ).execute().get("reviews", [])

        for review in reviews:
            name = review.get("authorName")
            comments = review.get("comments", [])
            review_time = 0
            for comment in comments:
                if comment.get("userComment"):
                    try:
                        review_time = int(comment.get("userComment").get("lastModified").get("seconds"))
                    except AttributeError:
                        continue
            if review_time < now() - MAX_REVIEW_DURATION_TIME:
                continue
            if name == user_identifier:
                return True
        return False
