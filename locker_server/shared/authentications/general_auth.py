from django.utils.encoding import smart_text
from rest_framework.authentication import BaseAuthentication, get_authorization_header


class GeneralAuthentication(BaseAuthentication):
    def authenticate(self, request):
        super(GeneralAuthentication, self).authenticate(request)

    def authenticate_header(self, request):
        return 'Bearer '

    def _get_token(self, request):
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

            if len(auth) != 2:
                return None

            token = auth[1].decode('utf-8')
            return token
        except Exception:
            return None
