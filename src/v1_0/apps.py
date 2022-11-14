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
    device_repository = CORE_CONFIG["repositories"]["IDeviceRepository"]()
    payment_repository = CORE_CONFIG["repositories"]["IPaymentRepository"]()
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()
    folder_repository = CORE_CONFIG["repositories"]["IFolderRepository"]()
    sharing_repository = CORE_CONFIG["repositories"]["ISharingRepository"]()
    team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
    team_member_repository = CORE_CONFIG["repositories"]["ITeamMemberRepository"]()
    collection_repository = CORE_CONFIG["repositories"]["ICollectionRepository"]()
    # group_repository = CORE_CONFIG["repositories"]["IGroupRepository"]()
    event_repository = CORE_CONFIG["repositories"]["IEventRepository"]()
    emergency_repository = CORE_CONFIG["repositories"]["IEmergencyAccessRepository"]()

    def check_pwd_session_auth(self, request):
        if request.auth:
            decoded_token = self.decode_token(request.auth)
            sso_token_id = decoded_token.get("sso_token_id") if decoded_token else None
        else:
            sso_token_id = None
        valid_token = self.device_repository.fetch_user_access_token(user=request.user, sso_token_id=sso_token_id)
        if not valid_token:
            raise AuthenticationFailed
        return valid_token

    def get_client_agent(self):
        return self.request.META.get("HTTP_LOCKER_CLIENT_AGENT")
