import json
import random

from datetime import datetime, timedelta
from typing import Dict, Union, Any

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, FloatField, ExpressionWrapper, Count, CharField, IntegerField
from django.db.models.expressions import RawSQL, Case, When
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from core.utils.data_helpers import camel_snake_data
from core.utils.core_helpers import secure_random_string
from cystack_models.models import Event
from cystack_models.models.notifications.notification_settings import NotificationSetting
from cystack_models.models.enterprises.enterprises import Enterprise
from shared.background import LockerBackgroundFactory, BG_EVENT, BG_NOTIFY
from shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD
from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from shared.constants.members import PM_MEMBER_STATUS_INVITED, MEMBER_ROLE_OWNER, PM_MEMBER_STATUS_CONFIRMED
from shared.constants.event import *
from shared.constants.policy import POLICY_TYPE_BLOCK_FAILED_LOGIN
from shared.constants.transactions import *
from shared.constants.user_notification import NOTIFY_SHARING, NOTIFY_CHANGE_MASTER_PASSWORD
from shared.error_responses.error import gen_error, refer_error
from shared.log.cylog import CyLog
from shared.permissions.locker_permissions.passwordless_pwd_permission import PasswordlessPwdPermission
from shared.permissions.locker_permissions.user_pwd_permission import UserPwdPermission
from shared.services.pm_sync import SYNC_EVENT_MEMBER_ACCEPTED, PwdSync, SYNC_EVENT_VAULT, SYNC_EVENT_MEMBER_UPDATE, \
    SYNC_EVENT_CIPHER_UPDATE
from shared.utils.app import now, start_end_month_current
from shared.utils.network import detect_device
from v1_0.ciphers.serializers import UpdateVaultItemSerializer, VaultItemSerializer
from v1_0.users.serializers import UserPwdSerializer, UserSessionSerializer, UserPwdInvitationSerializer, \
    UserMasterPasswordHashSerializer, UserChangePasswordSerializer, DeviceFcmSerializer, UserDeviceSerializer, \
    ListUserSerializer
from v1_0.apps import PasswordManagerViewSet


class PasswordlessPwdViewSet(PasswordManagerViewSet):
    permission_classes = (PasswordlessPwdPermission, )
    http_method_names = ["head", "options", "get", "post", ]

    def get_serializer_class(self):
        return super(PasswordlessPwdViewSet, self).get_serializer_class()

    @action(methods=["get", "post"], detail=False)
    def credential(self, request, *args, **kwargs):

        user = self.request.user

        CyLog.debug(**{"message": "Passwordless cred: {}".format(request.data)})

        if request.method == "GET":
            # TODO: Return cred id and a random 32-bytes  string
            # rad = random.

            return Response(status=200, data={"success": True})

        elif request.method == "POST":
            # TODO: Saving the cred id of the user
            pass
            return Response(status=200, data={"success": True})
