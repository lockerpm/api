import jwt

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from core.settings import CORE_CONFIG
from shared.authentications.general_auth import AppGeneralAuthentication
from shared.constants.token import TOKEN_PREFIX, TOKEN_TYPE_AUTHENTICATION


class LockerTokenAuthentication(AppGeneralAuthentication):
    user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()

    def authenticate(self, request):
        token_value = self._get_token(request)

        if token_value is None:
            return None
        # Remove token_prefix from token_value
        non_prefix_token = token_value[len(TOKEN_PREFIX):]

        try:
            payload = jwt.decode(non_prefix_token, settings.SECRET_KEY, algorithms=['HS256'])
            token_type = payload.get('token_type', None)
            user_id = payload.get('user_id', None)

            # Check token_type
            if (token_type != TOKEN_TYPE_AUTHENTICATION) or (user_id is None):
                return None

            # Get profile in token
            user_id = int(user_id)
            user = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
            return user, token_value

        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.exceptions.InvalidAlgorithmError,
                ValueError, ObjectDoesNotExist):
            return None
