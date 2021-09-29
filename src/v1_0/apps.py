from django.apps import AppConfig
from rest_framework.exceptions import AuthenticationFailed

from shared.general_view import AppGeneralViewSet


class V10Config(AppConfig):
    name = 'v1_0'


class PasswordManagerViewSet(AppGeneralViewSet):
    """
    This is a general view for Password Manager app
    """

    # def check_bw_auth(self, request, renew=False):
    #     valid_token = request.user.fetch_bw_access_token(renew=renew)
    #     if not valid_token:
    #         raise AuthenticationFailed
    #     return valid_token
