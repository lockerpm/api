from django.apps import AppConfig

from v1_0.general_view import PasswordManagerViewSet


class V1EnterpriseConfig(AppConfig):
    name = 'v1_enterprise'


class EnterpriseViewSet(PasswordManagerViewSet):
    """
    This is a general view for Enterprise app
    """
