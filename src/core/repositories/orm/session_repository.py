import jwt

from django.conf import settings

from core.repositories import ISessionRepository
from shared.utils.app import now
from cystack_models.models.users.users import User

from cystack_models.models.users.user_refresh_tokens import UserRefreshToken
from cystack_models.models.users.user_access_tokens import UserAccessToken


class SessionRepository(ISessionRepository):
    def fetch_valid_token(self, refresh_token: UserRefreshToken, renew: bool = False) -> UserAccessToken:
        """
        Get access token from exited refresh token
        :param refresh_token: (obj) UserRefreshToken object
        :param renew: (bool) if this value is True => Generate new refresh token instead of retrieving from database
        :return:
        """
        valid_access_token = UserAccessToken.objects.filter(
            refresh_token=refresh_token,  expired_time__gte=now()
        ).order_by('-expired_time').first()
        if not valid_access_token or renew is True:
            # Generate new access token
            valid_access_token = UserAccessToken.create(refresh_token, **{
                "access_token": self._gen_access_token_value(refresh_token=refresh_token),
                "grant_type": "refresh_token",
                "expired_time": now() + 3600
            })
        return valid_access_token

    def _gen_access_token_value(self, refresh_token: UserRefreshToken):
        created_time = now()
        expired_time = created_time + 3600
        payload = {
            "nbf": created_time,
            "exp": expired_time,
            "iss": "https://locker.io",
            # "user_id": refresh_token.user.user_id,
            "client_id": refresh_token.client_id,
            "sub": refresh_token.user.internal_id,
            "auth_time": created_time,
            "idp": "cystack",
            "email_verified": refresh_token.user.activated,
            "scope": ["api", "offline_access"],
            "jti": refresh_token.id,
            "device": refresh_token.device_identifier,
            "orgowner": "",
            "iat": created_time,
            "amr": ["Application"]
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
        return token

    def get_full_access_token(self, access_token: UserAccessToken):
        return "{} {}".format(access_token.refresh_token.token_type, access_token.access_token)

    def filter_refresh_tokens(self, user: User, device_identifier: str):
        return UserRefreshToken.objects.filter(device_identifier=device_identifier, user=user).order_by('-created_time')

    def fetch_access_token(self, user: User, renew: bool = False):
        refresh_token = user.user_refresh_tokens.all().order_by('-created_time').first()
        if not refresh_token:
            return None
        access_token = self.fetch_valid_token(refresh_token=refresh_token, renew=renew)
        return access_token
