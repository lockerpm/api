from django.conf import settings
from django.db.models import Value, When, Q, Case, IntegerField
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.background import *
from shared.constants.event import *
from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.emergency_access_pwd_permission import EmergencyAccessPermission
from shared.permissions.locker_permissions.member_pwd_permission import MemberPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_MEMBER_INVITATION, SYNC_EVENT_CIPHER, SYNC_EVENT_VAULT
from cystack_models.models.teams.teams import Team
from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.emergency_access.emergency_access import EmergencyAccess
from v1_0.emergency_access.serializers import EmergencyAccessGranteeSerializer, EmergencyAccessGrantorSerializer
from v1_0.apps import PasswordManagerViewSet


class EmergencyAccessPwdViewSet(PasswordManagerViewSet):
    permission_classes = (EmergencyAccessPermission, )
    lookup_value_regex = r'[0-9a-z\-]+'
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "trusted":
            self.serializer_class = EmergencyAccessGranteeSerializer
        elif self.action == "granted":
            self.serializer_class = EmergencyAccessGrantorSerializer
        return super(EmergencyAccessPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            emergency_access = self.emergency_repository.get_by_id(emergency_access_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=emergency_access)
            return emergency_access
        except EmergencyAccess.DoesNotExist:
            raise NotFound

    @action(methods=["get"], detail=False)
    def trusted(self, request, *args, **kwargs):
        user = self.request.user
        trusted_grantees = self.emergency_repository.get_multiple_by_grantor(grantor=user)
        serializer = self.get_serializer(trusted_grantees, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["get"], detail=False)
    def granted(self, request, *args, **kwargs):
        user = self.request.user
        granted_grantors = self.emergency_repository.get_multiple_by_grantee(grantee=user)
        serializer = self.get_serializer(granted_grantors, many=True)
        return Response(status=200, data=serializer.data)


