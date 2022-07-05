from django.apps import AppConfig

from shared.general_view import AppGeneralViewSet


class RelayConfig(AppConfig):
    name = 'relay'


class RelayViewSet(AppGeneralViewSet):
    """
    This is a general view for Relay app
    """

    def get_client_agent(self):
        return self.request.META.get("HTTP_LOCKER_CLIENT_AGENT")
