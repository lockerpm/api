from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField, Count, Avg
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.constants.ciphers import *
from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.group_pwd_permission import GroupPwdPermission
from shared.permissions.locker_permissions.team_pwd_permission import TeamPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_DELETE, SYNC_EVENT_CIPHER_CREATE, \
    SYNC_EVENT_CIPHER_UPDATE
from v1_0.enterprise.teams.serializers import ListTeamSerializer, UpdateTeamPwdSerializer
from v1_0.apps import PasswordManagerViewSet


class GroupPwdViewSet(PasswordManagerViewSet):
    permission_classes = (GroupPwdPermission, )
    http_method_names = ["head", "options", "get"]

    def get_serializer_class(self):
        return super(GroupPwdViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        pass

    def create(self, request, *args, **kwargs):
        pass

    def retrieve(self, request, *args, **kwargs):
        pass

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass

    @action(methods=["get", "put"], detail=False)
    def users(self, request, *args, **kwargs):
        pass
