from django.utils.encoding import smart_text
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from shared.constants.token import TOKEN_PREFIX


class AppGeneralAuthentication(BaseAuthentication):
    def authenticate(self, request):
        pass

    def authenticate_header(self, request):
        return 'Bearer'

    @staticmethod
    def _get_token(request):
        """
        :param request
        :return: token (has prefix `cs.`)
        """
        try:
            auth = get_authorization_header(request).split()
            auth_header_prefix = "Bearer"

            if not auth:
                return None

            # Check auth_header_prefix is `Bearer` token?
            if smart_text(auth[0].lower()) != auth_header_prefix.lower():
                return None

            if len(auth) == 1:
                return None
            elif len(auth) > 2:
                return None

            token = auth[1].decode('utf-8')
            if not token.startswith(TOKEN_PREFIX):
                return None

            return token  # Having `cs.`
        except (ValueError, KeyError, AttributeError):
            return None
