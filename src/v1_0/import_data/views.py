import json

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from core.utils.data_helpers import camel_snake_data
from shared.background import BG_EVENT, LockerBackgroundFactory, BG_CIPHER
from shared.constants.event import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.cipher_pwd_permission import CipherPwdPermission
from shared.permissions.locker_permissions.import_pwd_permission import ImportPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_VAULT
from v1_0.ciphers.serializers import VaultItemSerializer, UpdateVaultItemSerializer, \
    MutipleItemIdsSerializer, MultipleMoveSerializer, ShareVaultItemSerializer, ImportCipherSerializer, \
    SyncOfflineCipherSerializer, DetailCipherSerializer
from v1_0.apps import PasswordManagerViewSet


class ImportDataPwdViewSet(PasswordManagerViewSet):
    permission_classes = (ImportPwdPermission, )
    http_method_names = ["head", "options", "post"]

    def get_serializer_class(self):
        return super(ImportDataPwdViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def import_folders(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        folders = validated_data.get("folders", [])