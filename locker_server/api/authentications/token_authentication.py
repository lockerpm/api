from django.conf import settings
from jwt import ExpiredSignatureError

from locker_server.core.exceptions.user_exception import UserAuthFailedException
from locker_server.shared.authentications.app import AppGeneralAuthentication
from locker_server.containers.containers import auth_service


class TokenAuthentication(AppGeneralAuthentication):
    def authenticate(self, request):
        token_value = self._get_token(request)
        if not token_value:
            return None
        try:
            device_access_token = auth_service.check_device_access_token(
                access_token_value=token_value, secret=settings.SECRET_KEY, require_scopes=["api"]
            )
            return device_access_token.device.user, device_access_token
        except UserAuthFailedException:
            return None
        except ExpiredSignatureError:
            return None
