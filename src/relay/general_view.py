from core.settings import CORE_CONFIG
from shared.general_view import AppGeneralViewSet


class RelayViewSet(AppGeneralViewSet):
    """
    This is a general view for Relay app
    """
    user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()

    def get_client_agent(self):
        return self.request.META.get("HTTP_LOCKER_CLIENT_AGENT")
