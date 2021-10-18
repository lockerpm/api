from rest_framework.response import Response
from rest_framework.decorators import action

from micro_services.apps import MicroServiceViewSet
from shared.constants.members import MEMBER_ROLE_OWNER
from shared.permissions.micro_service_permissions.sync_permissions import SyncPermission
from cystack_models.models.teams.teams import Team
from cystack_models.models.members.member_roles import MemberRole


class ActivityLogViewSet(MicroServiceViewSet):
    permission_classes = ()
    http_method_names = ["head", "options", "post"]

    def get_serializer_class(self):
        return super(ActivityLogViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        pass
