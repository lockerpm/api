from django.apps import AppConfig

from shared.general_view import AppGeneralViewSet


class MicroServicesConfig(AppConfig):
    name = 'micro_services'


class MicroServiceViewSet(AppGeneralViewSet):
    """
    This is general view for micro_services app
    """
