from django.apps import AppConfig
from rest_framework.exceptions import AuthenticationFailed

from core.settings import CORE_CONFIG
from shared.general_view import AppGeneralViewSet


class V10Config(AppConfig):
    name = 'v1_0'


class PasswordManagerViewSet(AppGeneralViewSet):
    """
    This is a general view for Password Manager app
    """
    user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
    session_repository = CORE_CONFIG["repositories"]["ISessionRepository"]()
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()
    folder_repository = CORE_CONFIG["repositories"]["IFolderRepository"]()
    team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
    team_member_repository = CORE_CONFIG["repositories"]["ITeamMemberRepository"]()
    collection_repository = CORE_CONFIG["repositories"]["ICollectionRepository"]()
    payment_repository = CORE_CONFIG["repositories"]["IPaymentRepository"]()

    def check_pwd_session_auth(self, request, renew=False):
        valid_token = self.session_repository.fetch_access_token(user=request.user, renew=renew)
        if not valid_token:
            raise AuthenticationFailed
        return valid_token
