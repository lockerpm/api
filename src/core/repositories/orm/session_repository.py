from core.repositories import ISessionRepository
from shared.utils.app import now

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
            pass
        return valid_access_token

    def get_full_access_token(self, access_token: UserAccessToken):
        return "{} {}".format(access_token.refresh_token.token_type, access_token.access_token)
