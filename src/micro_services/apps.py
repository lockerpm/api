from django.apps import AppConfig

from core.settings import CORE_CONFIG
from shared.general_view import AppGeneralViewSet


class MicroServicesConfig(AppConfig):
    name = 'micro_services'


class MicroServiceViewSet(AppGeneralViewSet):
    """
    This is general view for micro_services app
    """
    user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
    team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
